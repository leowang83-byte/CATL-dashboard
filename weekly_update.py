import subprocess
import sys
from datetime import datetime


TASKS = [
    ("Build document market inputs", "document_market_inputs.py"),
    ("Update RSS lithium news", "rss_pipeline.py"),
    ("Update NewsAPI risk events", "news_pipeline.py"),
    ("Run main resource decision model", "main.py"),
    ("Build weekly decision actions", "weekly_decision_actions_generator.py"),
    ("Build LCE price forecast", "price_forecast.py"),
    ("Build LCE price time series", "price_timeseries.py"),
    ("Build LCE supply-demand forecast", "supply_demand_forecast.py"),
    ("Normalize dashboard CSV contracts", "normalize_dashboard_data.py"),
]


def run_task(task_name, script_name, allow_failure=False):
    print("")
    print("=" * 80)
    print(f"{datetime.now()} | {task_name}")
    print("=" * 80)

    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=True,
        text=True,
    )

    print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    if result.returncode != 0 and allow_failure:
        print(f"WARNING: Non-critical task failed: {task_name} ({script_name})")
        return False

    if result.returncode != 0:
        raise RuntimeError(f"Task failed: {task_name} ({script_name})")

    return True


def main():
    print("====== Weekly Lithium Price Forecast Update ======")

    for task_name, script_name in TASKS:
        allow_failure = script_name == "normalize_dashboard_data.py"
        run_task(task_name, script_name, allow_failure=allow_failure)

    print("")
    print("Weekly update completed successfully.")
    print("Generated files:")
    print("- reports/weekly_price_inputs.csv")
    print("- reports/lce_price_forecast.csv")
    print("- reports/dynamic_cost_curve.csv")
    print("- reports/investment_recommendations.csv")
    print("- reports/policy_price_impact.csv")
    print("- reports/weekly_market_signals.csv")
    print("- reports/weekly_decision_actions.csv")
    print("- reports/dashboard_data_health.csv")


if __name__ == "__main__":
    main()
