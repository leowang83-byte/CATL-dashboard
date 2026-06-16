from pathlib import Path

import pandas as pd

from database import load_resource_dataset, save_aisc_history
from market_data import fetch_open_source_indicators
from cost_curve import (
    build_resource_cost_table,
    calculate_aisc_90th,
    predict_lithium_spot_center,
)
from investment_engine import build_investment_recommendations
from event_risk import build_country_event_risk
from policy_impact import (
    generate_policy_events_from_news,
    apply_policy_shock_to_resource_table,
    estimate_policy_price_impact,
)


def main():
    print("====== Global Lithium Resource Decision System ======")

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    print("1. Loading PostgreSQL resource data...")
    mines, costs, policies, events = load_resource_dataset()

    print("2. Fetching market indicators...")
    lithium_futures_price, crude_oil_price = fetch_open_source_indicators()

    print("3. Building dynamic cost curve...")
    resource_cost_table = build_resource_cost_table(
        mines=mines,
        costs=costs,
        policies=policies,
        crude_oil_price=crude_oil_price,
    )

    print("3.1 Updating policy events from news...")
    generate_policy_events_from_news()

    print("3.2 Applying policy shock to capacity and AISC...")
    resource_cost_table = apply_policy_shock_to_resource_table(
        resource_cost_table
    )

    print("3.3 Integrating news-based country risk...")
    country_event_risk = build_country_event_risk()

    if not country_event_risk.empty:
        resource_cost_table = resource_cost_table.merge(
            country_event_risk,
            on="country",
            how="left"
        )
    else:
        resource_cost_table["event_risk_score"] = 0
        resource_cost_table["event_count"] = 0
        resource_cost_table["negative_event_count"] = 0
        resource_cost_table["latest_event_title"] = ""

    resource_cost_table["event_risk_score"] = (
        resource_cost_table["event_risk_score"].fillna(0)
    )
    resource_cost_table["event_count"] = (
        resource_cost_table["event_count"].fillna(0)
    )
    resource_cost_table["negative_event_count"] = (
        resource_cost_table["negative_event_count"].fillna(0)
    )
    resource_cost_table["latest_event_title"] = (
        resource_cost_table["latest_event_title"].fillna("")
    )

    if "risk_score" not in resource_cost_table.columns:
        resource_cost_table["risk_score"] = 0.5

    resource_cost_table["policy_risk_score"] = (
        resource_cost_table["risk_score"].fillna(0.5)
    )

    resource_cost_table["risk_score"] = (
        0.7 * resource_cost_table["policy_risk_score"]
        + 0.3 * resource_cost_table["event_risk_score"]
    ).clip(upper=1.0)

    print("4. Calculating AISC 90th percentile and base price center...")
    aisc_90th = calculate_aisc_90th(resource_cost_table)

    base_price_center = predict_lithium_spot_center(
        lithium_futures_price=lithium_futures_price,
        aisc_90th=aisc_90th,
    )

    print("4.1 Estimating policy impact on LCE price...")
    policy_price_impact = estimate_policy_price_impact(
        resource_cost_table=resource_cost_table,
        base_price_center=base_price_center,
    )

    expected_lce_price = policy_price_impact["expected_lce_price"]

    print("5. Generating investment recommendations...")
    recommendations = build_investment_recommendations(
        resource_cost_table,
        expected_lce_price
    )

    print("6. Saving dynamic AISC history to PostgreSQL...")
    save_aisc_history(resource_cost_table, crude_oil_price)

    print("7. Saving CSV reports...")

    resource_cost_table.to_csv(
        reports_dir / "dynamic_cost_curve.csv",
        index=False,
        encoding="utf-8-sig"
    )

    recommendations.to_csv(
        reports_dir / "investment_recommendations.csv",
        index=False,
        encoding="utf-8-sig"
    )

    if not country_event_risk.empty:
        country_event_risk.to_csv(
            reports_dir / "country_event_risk.csv",
            index=False,
            encoding="utf-8-sig"
        )
    else:
        pd.DataFrame(
            columns=[
                "country",
                "event_risk_score",
                "event_count",
                "negative_event_count",
                "latest_event_title",
            ]
        ).to_csv(
            reports_dir / "country_event_risk.csv",
            index=False,
            encoding="utf-8-sig"
        )

    pd.DataFrame([policy_price_impact]).to_csv(
        reports_dir / "policy_price_impact.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("")
    print("===== Core Output =====")
    print(f"GFEX lithium futures price: {lithium_futures_price}")
    print(f"Crude oil shadow price: {crude_oil_price}")
    print(f"Dynamic 90% AISC floor: {round(aisc_90th, 2)}")
    print(f"Base lithium spot center: {base_price_center}")
    print(f"Expected LCE price after policy impact: {expected_lce_price}")
    print(f"Supply loss ratio: {policy_price_impact.get('supply_loss_ratio')}")
    print(f"AISC uplift from policy: {policy_price_impact.get('aisc_uplift')}")
    print("")
    print("Reports saved:")
    print("- reports/dynamic_cost_curve.csv")
    print("- reports/investment_recommendations.csv")
    print("- reports/country_event_risk.csv")
    print("- reports/policy_price_impact.csv")
    print("")
    print("AISC history saved to PostgreSQL table:")
    print("- aisc_history")
    print("")
    print("Top recommendations:")
    print(recommendations.head(5).to_string(index=False))


if __name__ == "__main__":
    main()