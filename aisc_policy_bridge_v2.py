from datetime import date
from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")

AISCPATH = REPORTS_DIR / "dynamic_cost_curve.csv"
POLICYPATH = REPORTS_DIR / "lithium_policy_decomposed_risk.csv"

OUTPUT = REPORTS_DIR / "project_strategic_aisc_v2.csv"

LCE_PRICE = 18.2


def load():
    if not AISCPATH.exists():
        return pd.DataFrame(), pd.DataFrame()

    aisc = pd.read_csv(AISCPATH, encoding="utf-8-sig")

    if POLICYPATH.exists():
        pol = pd.read_csv(POLICYPATH, encoding="utf-8-sig")
    else:
        pol = pd.DataFrame()

    return aisc, pol


def to_wan(value):
    value = pd.to_numeric(value, errors="coerce").fillna(0)
    return value / 10000


def get_country_risk(pol):
    if pol.empty or "country" not in pol.columns or "risk_score" not in pol.columns:
        return {}

    pol = pol.copy()
    pol["risk_score"] = pd.to_numeric(pol["risk_score"], errors="coerce").fillna(0)
    return pol.groupby("country")["risk_score"].max().to_dict()


def normalize_country(value):
    country = str(value or "").strip()
    aliases = {
        "People's Republic of China": "China",
        "Democratic Republic of the Congo": "Democratic Republic of Congo",
        "DRC": "Democratic Republic of Congo",
        "USA": "United States",
        "United States of America": "United States",
    }
    return aliases.get(country, country)


def compute(df, pol):
    df = df.copy()
    valid_policy_df = (
        not pol.empty
        and {"country", "policy_type", "risk_score"}.issubset(set(pol.columns))
    )
    if valid_policy_df:
        pol = pol.copy()
        pol["country_match"] = pol["country"].apply(normalize_country)
        pol["risk_score"] = pd.to_numeric(pol["risk_score"], errors="coerce").fillna(0)
        country_risk = pol.groupby("country_match")["risk_score"].max().to_dict()
    else:
        country_risk = {}

    if "project" not in df.columns:
        df["project"] = df.get("name", df.get("project_name", ""))
    if "project_name" not in df.columns:
        df["project_name"] = df.get("project", df.get("name", ""))
    if "company" not in df.columns:
        df["company"] = df.get("owner", "")

    base_source = df.get("aisc_cost", df.get("adjusted_aisc", 0))
    adjusted_source = df.get(
        "adjusted_aisc",
        df.get("realtime_aisc", df.get("delivered_cost", base_source)),
    )
    df["base_aisc_wan"] = to_wan(base_source)
    df["adjusted_aisc_wan"] = to_wan(adjusted_source)
    df["strategy_base_aisc_wan"] = (
        df[["base_aisc_wan", "adjusted_aisc_wan"]].max(axis=1)
    )

    def dominant_policy_type(country):
        if not valid_policy_df:
            return "unknown"
        country_rows = pol[pol["country_match"] == normalize_country(country)]
        if country_rows.empty:
            return "unknown"
        max_risk = country_rows["risk_score"].max()
        high_risk_rows = country_rows[country_rows["risk_score"] == max_risk]
        mode_value = high_risk_rows["policy_type"].mode()
        return mode_value.iloc[0] if len(mode_value) else "unknown"

    def premium(row):
        if not valid_policy_df:
            return 0.0

        country = row.get("country", "")
        risk_score = country_risk.get(normalize_country(country), 0.0)
        if risk_score <= 0:
            return 0.0
        policy_type = dominant_policy_type(country)

        base = {
            "export_control": 0.18,
            "local_processing": 0.15,
            "state_control": 0.12,
            "tax_royalty": 0.10,
            "environment_policy": 0.08,
            "investment_restriction": 0.08,
            "permitting": 0.06,
            "subsidy_support": -0.02,
        }.get(policy_type, 0.03)

        if risk_score >= 0.85:
            factor = 1.30
        elif risk_score >= 0.70:
            factor = 1.15
        elif risk_score >= 0.55:
            factor = 1.00
        elif risk_score >= 0.40:
            factor = 0.60
        else:
            factor = 0.30

        return base * factor

    df["country_match"] = df.get("country", pd.Series("", index=df.index)).apply(normalize_country)
    df["policy_risk_score"] = df["country_match"].map(country_risk).fillna(0)
    df["policy_risk_premium_pct"] = df.apply(premium, axis=1)
    df["policy_risk_premium_wan"] = (
        df["strategy_base_aisc_wan"] * df["policy_risk_premium_pct"]
    )
    df["strategic_aisc_wan"] = (
        df["strategy_base_aisc_wan"] + df["policy_risk_premium_wan"]
    )
    df["adjusted_minus_base_wan"] = df["adjusted_aisc_wan"] - df["base_aisc_wan"]
    df["strategic_minus_adjusted_wan"] = (
        df["strategic_aisc_wan"] - df["adjusted_aisc_wan"]
    )
    df["strategic_aisc_wan"] = (
        df[["strategic_aisc_wan", "adjusted_aisc_wan"]].max(axis=1)
    )
    df["strategic_minus_adjusted_wan"] = (
        df["strategic_aisc_wan"] - df["adjusted_aisc_wan"]
    )
    df["price_margin_wan"] = LCE_PRICE - df["strategic_aisc_wan"]

    def investable_label(margin):
        if margin > 5:
            return "\u6838\u5fc3\u914d\u7f6e"
        if margin > 0:
            return "\u53ef\u6295\u8d44\u89c2\u5bdf"
        return "\u9ad8\u98ce\u9669"

    df["is_investable"] = df["price_margin_wan"].apply(investable_label)
    df["adjustment_reason"] = (
        "\u6218\u7565AISC=\u6218\u7565\u57fa\u51c6AISC+\u653f\u7b56\u98ce\u9669\u6ea2\u4ef7\uff1b"
        "\u6218\u7565\u57fa\u51c6AISC\u53d6\u539f\u59cbAISC\u4e0e\u8c03\u6574\u540eAISC\u7684\u8f83\u9ad8\u503c\uff0c"
        "\u907f\u514d\u4f4e\u4f30\u8d44\u6e90\u53ef\u83b7\u5f97\u6210\u672c\u3002"
    )
    if not valid_policy_df:
        df["adjustment_reason"] = (
            "\u672a\u63a5\u5165\u6709\u6548\u9502\u76f8\u5173\u653f\u7b56\u5206\u89e3\u98ce\u9669\uff0c"
            "\u672c\u6b21\u6218\u7565AISC\u6682\u4e0d\u52a0\u653f\u7b56\u6ea2\u4ef7\u3002"
        )

    df["last_updated"] = str(date.today())

    return df


def main():
    aisc, pol = load()

    if aisc.empty:
        print("No AISC data")
        return

    out = compute(aisc, pol)
    out.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("projects:", len(out))
    print("matched policy risk projects:", int((out["policy_risk_score"] > 0).sum()))
    print("unmatched policy risk projects:", int((out["policy_risk_score"] <= 0).sum()))
    print("saved:", OUTPUT)


if __name__ == "__main__":
    main()
