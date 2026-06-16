import hashlib
from datetime import datetime
from pathlib import Path

import feedparser

from database import get_connection
from news_pipeline import (
    ensure_event_data_table,
    build_country_event_risk,
    build_news_event_summary,
    clean_title,
    is_relevant_lithium_resource_news,
    detect_country,
    classify_event,
    make_hash,
    make_title_hash,
    translate_title_to_chinese,
)


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# =========================
# 免费 RSS 新闻源
# =========================
# 先用少量高质量 RSS，跑稳定后再扩展。
# 如果某个 feed 失效，不影响其他 feed。
# =========================

RSS_FEEDS = [
    {
        "name": "MINING.com",
        "url": "https://www.mining.com/feed/",
        "source_type": "mining_news",
    },
    {
        "name": "GlobeNewswire - Press Releases",
        "url": "https://www.globenewswire.com/RssFeed/subjectcode/0/feedTitle/GlobeNewswire%20-%20News%20about%20Public%20Companies",
        "source_type": "press_release",
    },
    {
        "name": "PR Newswire - News Releases",
        "url": "https://www.prnewswire.com/rss/news-releases-list.rss",
        "source_type": "press_release",
    },
]


def normalize_text(value):
    if value is None:
        return ""
    return str(value).lower()


def rss_entry_id(title, link):
    raw = f"{title}|{link}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_entry_published_at(entry):
    """
    尽量从 RSS entry 中提取发布时间。
    提取不到则使用当前时间。
    """
    if getattr(entry, "published", None):
        return entry.published

    if getattr(entry, "updated", None):
        return entry.updated

    return datetime.now().isoformat()


def entry_exists_by_url_or_title_hash(cur, url, title_hash):
    cur.execute(
        """
        SELECT id FROM event_data
        WHERE url = %s OR title_hash = %s
        LIMIT 1;
        """,
        (url, title_hash),
    )
    return cur.fetchone() is not None


def insert_rss_event(entry, feed_name):
    raw_title = getattr(entry, "title", "") or ""
    title = clean_title(raw_title)

    link = getattr(entry, "link", "") or ""
    summary = getattr(entry, "summary", "") or ""

    if not title or not link:
        return False

    if not is_relevant_lithium_resource_news(title, summary):
        return False

    country = detect_country(title, summary)
    event_info = classify_event(title, summary)

    title_hash = make_title_hash(title)
    event_hash = make_hash(title, link)
    title_cn = translate_title_to_chinese(title)
    published_at = get_entry_published_at(entry)

    conn = get_connection()
    cur = conn.cursor()

    try:
        if entry_exists_by_url_or_title_hash(cur, link, title_hash):
            conn.rollback()
            return False

        cur.execute(
            """
            INSERT INTO event_data (
                title,
                title_cn,
                source,
                url,
                keyword,
                country,
                published_at,
                risk_score,
                impact_direction,
                event_type,
                supply_shock,
                price_shock,
                event_hash,
                title_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (
                title,
                title_cn,
                feed_name,
                link,
                "rss",
                country,
                published_at,
                event_info["risk_score"],
                event_info["impact_direction"],
                event_info["event_type"],
                event_info["supply_shock"],
                event_info["price_shock"],
                event_hash,
                title_hash,
            ),
        )

        inserted = cur.rowcount > 0
        conn.commit()

    except Exception as exc:
        print("RSS insert error:", exc)
        conn.rollback()
        inserted = False

    finally:
        cur.close()
        conn.close()

    return inserted


def fetch_rss_feed(feed):
    name = feed["name"]
    url = feed["url"]

    print(f"Fetching RSS: {name} | {url}")

    parsed = feedparser.parse(url)

    if getattr(parsed, "bozo", False):
        print(f"RSS parse warning for {name}: {getattr(parsed, 'bozo_exception', '')}")

    entries = getattr(parsed, "entries", []) or []

    print(f"RSS entries fetched from {name}: {len(entries)}")

    return entries


def main():
    ensure_event_data_table()

    total_entries = 0
    total_relevant = 0
    total_inserted = 0

    for feed in RSS_FEEDS:
        entries = fetch_rss_feed(feed)
        total_entries += len(entries)

        for entry in entries:
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""

            if is_relevant_lithium_resource_news(title, summary):
                total_relevant += 1

            if insert_rss_event(entry, feed["name"]):
                total_inserted += 1

    print("RSS total entries:", total_entries)
    print("RSS relevant entries:", total_relevant)
    print("RSS inserted entries:", total_inserted)

    risk_df = build_country_event_risk()
    summary_df = build_news_event_summary()

    print("Saved reports/country_event_risk.csv")
    print(risk_df.head(20).to_string(index=False))

    print("Saved reports/news_event_summary.csv")
    print(summary_df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()