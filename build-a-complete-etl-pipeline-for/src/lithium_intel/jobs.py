from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import psycopg

from lithium_intel.config import Settings
from lithium_intel.db import finish_run, get_conn, start_run
from lithium_intel.news_api import NewsApiClient
from lithium_intel.risk import calculate_project_risk
from lithium_intel.transforms import load_csv_rows, normalize_news_article


logger = logging.getLogger(__name__)


def fetch_news(settings: Settings) -> int:
    settings.validate_for_database()
    settings.validate_for_news()
    client = NewsApiClient(settings.newsapi_key)
    articles = client.fetch_lithium_news(
        query=settings.news_query,
        language=settings.news_language,
        page_size=settings.news_page_size,
    )
    normalized = [row for row in (normalize_news_article(article) for article in articles) if row.get("url")]

    with get_conn(settings.database_url) as conn:
        run_id = start_run(conn, "fetch_news")
        try:
            count = upsert_event_data(conn, normalized)
            finish_run(conn, run_id, "success", count)
            logger.info("Fetched and loaded %s lithium news records", count)
            return count
        except Exception as exc:
            finish_run(conn, run_id, "failed", 0, str(exc))
            logger.exception("News fetch failed")
            raise


def update_mining_projects(settings: Settings) -> int:
    settings.validate_for_database()
    seed_rows = load_csv_rows(settings.project_seed_path)

    with get_conn(settings.database_url) as conn:
        run_id = start_run(conn, "update_mining_projects")
        try:
            count = upsert_mining_projects(conn, seed_rows)
            enrich_projects_from_news(conn)
            finish_run(conn, run_id, "success", count)
            logger.info("Updated %s mining projects", count)
            return count
        except Exception as exc:
            finish_run(conn, run_id, "failed", 0, str(exc))
            logger.exception("Mining project update failed")
            raise


def update_cost_curve(settings: Settings) -> int:
    settings.validate_for_database()
    source_rows = load_csv_rows(settings.cost_curve_source_path)

    with get_conn(settings.database_url) as conn:
        run_id = start_run(conn, "update_cost_curve")
        try:
            count = upsert_cost_curve(conn, source_rows)
            update_cost_percentiles(conn)
            finish_run(conn, run_id, "success", count)
            logger.info("Updated %s cost curve rows", count)
            return count
        except Exception as exc:
            finish_run(conn, run_id, "failed", 0, str(exc))
            logger.exception("Cost curve update failed")
            raise


def generate_daily_risk_scores(settings: Settings, score_date: date | None = None) -> int:
    settings.validate_for_database()
    score_date = score_date or date.today()

    with get_conn(settings.database_url) as conn:
        run_id = start_run(conn, "generate_daily_risk_scores")
        try:
            projects = fetch_projects(conn)
            count = 0
            for project in projects:
                events = fetch_recent_events(conn, project)
                cost_row = fetch_latest_cost_row(conn, project["id"])
                risk = calculate_project_risk(project, events, cost_row)
                upsert_risk_score(conn, project["id"], score_date, risk)
                count += 1
            finish_run(conn, run_id, "success", count)
            logger.info("Generated %s daily risk scores", count)
            return count
        except Exception as exc:
            finish_run(conn, run_id, "failed", 0, str(exc))
            logger.exception("Risk score generation failed")
            raise


def run_daily(settings: Settings) -> dict[str, int]:
    results = {
        "news_records": fetch_news(settings),
        "projects": update_mining_projects(settings),
        "cost_curve_rows": update_cost_curve(settings),
        "risk_scores": generate_daily_risk_scores(settings),
    }
    logger.info("Daily ETL complete: %s", results)
    return results


def upsert_event_data(conn: psycopg.Connection, rows: list[dict]) -> int:
    if not rows:
        return 0
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                """
                INSERT INTO event_data (
                    source, author, title, description, content, url, image_url, published_at,
                    raw_payload, commodity, region, country, project_name, event_type, sentiment_score
                )
                VALUES (
                    %(source)s, %(author)s, %(title)s, %(description)s, %(content)s, %(url)s, %(image_url)s,
                    %(published_at)s, %(raw_payload)s::jsonb, %(commodity)s, %(region)s, %(country)s,
                    %(project_name)s, %(event_type)s, %(sentiment_score)s
                )
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    content = EXCLUDED.content,
                    published_at = EXCLUDED.published_at,
                    raw_payload = EXCLUDED.raw_payload,
                    country = EXCLUDED.country,
                    project_name = EXCLUDED.project_name,
                    event_type = EXCLUDED.event_type,
                    sentiment_score = EXCLUDED.sentiment_score
                """,
                row,
            )
    return len(rows)


def upsert_mining_projects(conn: psycopg.Connection, rows: list[dict[str, str]]) -> int:
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                """
                INSERT INTO mining_projects (
                    project_name, country, region, owner_company, resource_type, status,
                    estimated_resource_mt_lce, annual_capacity_t_lce, expected_start_year, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (project_name, country) DO UPDATE SET
                    region = EXCLUDED.region,
                    owner_company = EXCLUDED.owner_company,
                    resource_type = EXCLUDED.resource_type,
                    status = EXCLUDED.status,
                    estimated_resource_mt_lce = EXCLUDED.estimated_resource_mt_lce,
                    annual_capacity_t_lce = EXCLUDED.annual_capacity_t_lce,
                    expected_start_year = EXCLUDED.expected_start_year,
                    updated_at = NOW()
                """,
                (
                    row["project_name"],
                    row["country"],
                    row.get("region"),
                    row.get("owner_company"),
                    row.get("resource_type"),
                    row.get("status"),
                    _decimal_or_none(row.get("estimated_resource_mt_lce")),
                    _decimal_or_none(row.get("annual_capacity_t_lce")),
                    _int_or_none(row.get("expected_start_year")),
                ),
            )
    return len(rows)


def enrich_projects_from_news(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE mining_projects p
            SET last_news_at = news.last_news_at,
                risk_signal_count = news.risk_signal_count,
                updated_at = NOW()
            FROM (
                SELECT
                    project_name,
                    country,
                    MAX(published_at) AS last_news_at,
                    COUNT(*) FILTER (
                        WHERE event_type IN ('disruption', 'permitting') OR sentiment_score < 0
                    ) AS risk_signal_count
                FROM event_data
                WHERE published_at >= NOW() - INTERVAL '30 days'
                  AND project_name IS NOT NULL
                  AND country IS NOT NULL
                GROUP BY project_name, country
            ) news
            WHERE LOWER(p.project_name) = LOWER(news.project_name)
              AND p.country = news.country
            """
        )


def upsert_cost_curve(conn: psycopg.Connection, rows: list[dict[str, str]]) -> int:
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                """
                SELECT id FROM mining_projects
                WHERE LOWER(project_name) = LOWER(%s) AND country = %s
                """,
                (row["project_name"], row["country"]),
            )
            project = cur.fetchone()
            if not project:
                logger.warning("Skipping cost row for unknown project: %s, %s", row["project_name"], row["country"])
                continue
            cur.execute(
                """
                INSERT INTO cost_curve (
                    project_id, as_of_date, cash_cost_usd_t_lce, sustaining_cost_usd_t_lce,
                    all_in_cost_usd_t_lce, production_t_lce, source, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (project_id, as_of_date) DO UPDATE SET
                    cash_cost_usd_t_lce = EXCLUDED.cash_cost_usd_t_lce,
                    sustaining_cost_usd_t_lce = EXCLUDED.sustaining_cost_usd_t_lce,
                    all_in_cost_usd_t_lce = EXCLUDED.all_in_cost_usd_t_lce,
                    production_t_lce = EXCLUDED.production_t_lce,
                    source = EXCLUDED.source,
                    updated_at = NOW()
                """,
                (
                    project["id"],
                    row["as_of_date"],
                    _decimal_or_none(row.get("cash_cost_usd_t_lce")),
                    _decimal_or_none(row.get("sustaining_cost_usd_t_lce")),
                    _decimal_or_none(row.get("all_in_cost_usd_t_lce")),
                    _decimal_or_none(row.get("production_t_lce")),
                    row.get("source"),
                ),
            )
    return len(rows)


def update_cost_percentiles(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH ranked AS (
                SELECT
                    id,
                    CASE
                        WHEN COUNT(*) OVER () = 1 THEN 0.5
                        ELSE PERCENT_RANK() OVER (ORDER BY all_in_cost_usd_t_lce)
                    END AS percentile
                FROM cost_curve
                WHERE as_of_date = (SELECT MAX(as_of_date) FROM cost_curve)
                  AND all_in_cost_usd_t_lce IS NOT NULL
            )
            UPDATE cost_curve c
            SET cost_percentile = ranked.percentile,
                updated_at = NOW()
            FROM ranked
            WHERE c.id = ranked.id
            """
        )


def fetch_projects(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM mining_projects ORDER BY project_name")
        return list(cur.fetchall())


def fetch_recent_events(conn: psycopg.Connection, project: dict) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=30)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM event_data
            WHERE published_at >= %s
              AND (
                LOWER(project_name) = LOWER(%s)
                OR country = %s
              )
            ORDER BY published_at DESC
            LIMIT 100
            """,
            (since, project["project_name"], project["country"]),
        )
        return list(cur.fetchall())


def fetch_latest_cost_row(conn: psycopg.Connection, project_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM cost_curve
            WHERE project_id = %s
            ORDER BY as_of_date DESC
            LIMIT 1
            """,
            (project_id,),
        )
        return cur.fetchone()


def upsert_risk_score(conn: psycopg.Connection, project_id: int, score_date: date, risk: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO risk_scores (
                project_id, score_date, operational_risk, jurisdiction_risk, market_risk,
                news_risk, total_risk, rationale
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (project_id, score_date) DO UPDATE SET
                operational_risk = EXCLUDED.operational_risk,
                jurisdiction_risk = EXCLUDED.jurisdiction_risk,
                market_risk = EXCLUDED.market_risk,
                news_risk = EXCLUDED.news_risk,
                total_risk = EXCLUDED.total_risk,
                rationale = EXCLUDED.rationale
            """,
            (
                project_id,
                score_date,
                risk["operational_risk"],
                risk["jurisdiction_risk"],
                risk["market_risk"],
                risk["news_risk"],
                risk["total_risk"],
                json.dumps(risk["rationale"]),
            ),
        )


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(value)


def _int_or_none(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(value)

