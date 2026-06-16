from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")
OUTPUT = REPORTS_DIR / "policy_adjusted_price_scenarios_2026_2035.csv"

YEARS = list(range(2026, 2036))

ORIGINAL_PRICE = {
    "STEPS": [12.0, 12.0, 12.0, 12.0, 12.0, 12.0, 12.0, 12.0, 12.0, 13.0],
    "APS": [18.0, 19.0, 20.0, 21.0, 21.0, 21.0, 22.0, 22.0, 23.0, 23.0],
    "NZE": [25.0, 27.0, 28.0, 30.0, 31.0, 32.0, 32.0, 33.0, 33.0, 34.0],
}

POLICY_ADJUSTED_PRICE = {
    "STEPS": [12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.0, 15.5, 15.5, 16.0],
    "APS": [18.5, 20.0, 21.5, 23.0, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5],
    "NZE": [26.0, 28.5, 30.5, 33.0, 34.5, 35.5, 36.5, 37.5, 38.0, 39.0],
}

SUPPLY_REALIZATION_RATE = {
    "STEPS": [0.98, 0.98, 0.97, 0.97, 0.96, 0.96, 0.96, 0.95, 0.95, 0.95],
    "APS": [0.97, 0.97, 0.96, 0.95, 0.94, 0.94, 0.93, 0.93, 0.92, 0.92],
    "NZE": [0.96, 0.95, 0.94, 0.93, 0.92, 0.92, 0.91, 0.91, 0.90, 0.90],
}

ADJUSTMENT_REASON = {
    "STEPS": (
        "纳入IEA政策约束后，即使在保守需求情景下，出口限制、本地加工要求、"
        "审批和环保约束仍会降低部分名义供给兑现率，因此价格中枢小幅上修。"
    ),
    "APS": (
        "APS为核心基准情景。纳入IEA政策约束后，资源国出口限制、本地加工、"
        "国家参与和审批环保约束会推迟新增供给释放，因此2028年后价格中枢明显上修。"
    ),
    "NZE": (
        "NZE为高需求低容错情景。政策约束对供给释放的影响被放大，"
        "供需缺口扩大，长期价格中枢显著上修。"
    ),
}


def build_policy_adjusted_price_scenarios():
    rows = []

    for scenario in ["STEPS", "APS", "NZE"]:
        for idx, year in enumerate(YEARS):
            original_price = ORIGINAL_PRICE[scenario][idx]
            adjusted_price = POLICY_ADJUSTED_PRICE[scenario][idx]
            realization_rate = SUPPLY_REALIZATION_RATE[scenario][idx]
            price_uplift = adjusted_price - original_price
            uplift_pct = price_uplift / original_price if original_price > 0 else 0
            constraint_factor = 1 - realization_rate

            rows.append(
                {
                    "year": year,
                    "scenario": scenario,
                    "price_center_original_wan": original_price,
                    "policy_adjusted_price_center_wan": adjusted_price,
                    "policy_price_uplift_wan": price_uplift,
                    "policy_price_uplift_pct": uplift_pct,
                    "policy_supply_realization_rate": realization_rate,
                    "policy_supply_constraint_factor": constraint_factor,
                    "adjustment_reason": ADJUSTMENT_REASON[scenario],
                }
            )

    return pd.DataFrame(rows)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = build_policy_adjusted_price_scenarios()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"写入: {OUTPUT}")
    print(f"记录数: {len(df)}")
    print(df.groupby("scenario")["policy_price_uplift_wan"].agg(["min", "max", "mean"]))


if __name__ == "__main__":
    main()
