from __future__ import annotations

import argparse
import logging

from lithium_intel.config import Settings
from lithium_intel.jobs import fetch_news, generate_daily_risk_scores, run_daily, update_cost_curve, update_mining_projects
from lithium_intel.logging_config import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lithium resource intelligence ETL")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("fetch-news", help="Fetch lithium news from NewsAPI and load event_data")
    subparsers.add_parser("update-projects", help="Refresh mining_projects")
    subparsers.add_parser("update-cost-curve", help="Refresh cost_curve")
    subparsers.add_parser("score-risks", help="Generate daily risk scores")
    subparsers.add_parser("run-daily", help="Run the complete daily ETL")
    return parser


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_dir, settings.log_level)
    logger = logging.getLogger(__name__)
    args = build_parser().parse_args()

    if args.command == "fetch-news":
        result = fetch_news(settings)
    elif args.command == "update-projects":
        result = update_mining_projects(settings)
    elif args.command == "update-cost-curve":
        result = update_cost_curve(settings)
    elif args.command == "score-risks":
        result = generate_daily_risk_scores(settings)
    elif args.command == "run-daily":
        result = run_daily(settings)
    else:
        raise ValueError(f"Unsupported command: {args.command}")

    logger.info("Command %s finished with result: %s", args.command, result)


if __name__ == "__main__":
    main()

