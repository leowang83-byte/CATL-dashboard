# Global Lithium Resource Intelligence ETL

Python ETL pipeline for collecting lithium market news, loading it into PostgreSQL, refreshing mining project and cost curve intelligence, and producing daily project risk scores.

## Features

- Fetches lithium news from NewsAPI.
- Stores normalized news records in `event_data`.
- Refreshes `mining_projects` daily from project seed data and news signals.
- Updates `cost_curve` from a configurable CSV source.
- Generates daily risk scores into `risk_scores`.
- Writes rotating logs to `logs/lithium_etl.log`.
- Provides CLI commands for one-off runs and scheduler-friendly daily execution.

## Project Layout

```text
.
├── config/
│   ├── mining_projects.seed.csv
│   └── cost_curve.seed.csv
├── logs/
│   └── .gitkeep
├── sql/
│   └── schema.sql
├── src/
│   └── lithium_intel/
│       ├── cli.py
│       ├── config.py
│       ├── db.py
│       ├── jobs.py
│       ├── logging_config.py
│       ├── news_api.py
│       ├── risk.py
│       └── transforms.py
├── tests/
│   └── test_risk.py
├── .env.example
├── pyproject.toml
└── requirements.txt
```

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create PostgreSQL tables:

```bash
psql "$DATABASE_URL" -f sql/schema.sql
```

3. Copy `.env.example` to `.env` or export the variables in your scheduler:

```bash
NEWSAPI_KEY=your_newsapi_key
DATABASE_URL=postgresql://user:password@localhost:5432/lithium_intel
```

## Usage

Run the full daily pipeline:

```bash
python -m lithium_intel.cli run-daily
```

Run individual jobs:

```bash
python -m lithium_intel.cli fetch-news
python -m lithium_intel.cli update-projects
python -m lithium_intel.cli update-cost-curve
python -m lithium_intel.cli score-risks
```

## Scheduling

Use cron, Windows Task Scheduler, Airflow, or another orchestrator to run:

```bash
python -m lithium_intel.cli run-daily
```

The command is idempotent for daily use. News articles are deduplicated by URL, project rows are upserted by `(project_name, country)`, cost curve rows are upserted by `(project_id, as_of_date)`, and risk scores are upserted by `(project_id, score_date)`.

