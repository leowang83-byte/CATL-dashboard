import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


def get_db_config():
    load_dotenv()

    db_config = {
        "host": os.getenv("PGHOST", "127.0.0.1"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
    }

    missing = [key for key, value in db_config.items() if not value]
    if missing:
        raise RuntimeError(f"Missing database config in .env: {missing}")

    return db_config


def load_events():
    db_config = get_db_config()

    query = """
    SELECT
        id,
        title,
        source,
        url,
        keyword,
        risk_score,
        impact_direction,
        created_at
    FROM event_data
    ORDER BY created_at DESC;
    """

    with psycopg2.connect(**db_config) as conn:
        df = pd.read_sql_query(query, conn)

    return df


def build_summary(df):
    total_events = len(df)

    high_risk_events = df[df["risk_score"] >= 0.7]
    negative_events = df[df["impact_direction"] == "negative"]

    summary = {
        "total_events": total_events,
        "high_risk_events": len(high_risk_events),
        "negative_events": len(negative_events),
        "average_risk_score": round(df["risk_score"].fillna(0).mean(), 3) if total_events > 0 else 0,
    }

    return summary, high_risk_events


def save_outputs(summary, high_risk_events):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(reports_dir / "risk_summary.csv", index=False, encoding="utf-8-sig")

    high_risk_events.head(10).to_csv(
        reports_dir / "latest_high_risk_events.csv",
        index=False,
        encoding="utf-8-sig"
    )


def main():
    df = load_events()

    if df.empty:
        print("No events found in event_data.")
        return

    summary, high_risk_events = build_summary(df)
    save_outputs(summary, high_risk_events)

    print("===== Lithium Risk Summary =====")
    print(f"Total events: {summary['total_events']}")
    print(f"High risk events: {summary['high_risk_events']}")
    print(f"Negative events: {summary['negative_events']}")
    print(f"Average risk score: {summary['average_risk_score']}")
    print("")
    print("Reports saved:")
    print("- reports/risk_summary.csv")
    print("- reports/latest_high_risk_events.csv")


if __name__ == "__main__":
    main()