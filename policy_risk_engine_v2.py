from datetime import date
from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")

INPUT_CANDIDATES = [
    REPORTS_DIR / "lithium_policy_scored_table.csv",
    REPORTS_DIR / "policy_scored_table.csv",
    REPORTS_DIR / "lithium_policy_master_table.csv",
    REPORTS_DIR / "policy_master_table.csv",
    REPORTS_DIR / "critical_minerals_policy_tracker.csv",
]
OUTPUT_PATH = REPORTS_DIR / "lithium_policy_decomposed_risk.csv"
PROJECT_COUNTRY_PATH = REPORTS_DIR / "dynamic_cost_curve.csv"

REQUIRED_OUTPUT_COLUMNS = [
    "policy_id",
    "country",
    "policy_name",
    "policy_type",
    "risk_score",
    "policy_base_impact",
    "policy_intensity",
    "policy_risk_premium_pct",
    "export_pressure",
    "processing_pressure",
    "fiscal_pressure",
    "delay_pressure",
    "last_updated",
]

LITHIUM_KEYWORDS = [
    "lithium",
    "spodumene",
    "lithium concentrate",
    "lithium carbonate",
    "lithium hydroxide",
    "brine",
    "salar",
    "salt lake",
    "lce",
    "li-ion",
    "lithium-ion",
    "\u9502",
    "\u9502\u77ff",
    "\u9502\u8f89\u77f3",
    "\u9502\u7cbe\u77ff",
    "\u78b3\u9178\u9502",
    "\u6c22\u6c27\u5316\u9502",
    "\u76d0\u6e56\u9502",
    "\u5364\u6c34\u9502",
    "\u9502\u7535\u6c60",
]

NON_LITHIUM_MINERALS = [
    "nickel",
    "copper",
    "cobalt",
    "graphite",
    "rare earth",
    "manganese",
    "aluminium",
    "iron ore",
    "coal",
    "uranium",
    "\u954d",
    "\u94dc",
    "\u94b4",
    "\u77f3\u58a8",
    "\u7a00\u571f",
    "\u9530",
    "\u94dd",
    "\u94c1\u77ff",
    "\u7164\u70ad",
    "\u94c0",
]

POLICY_TYPE_MAP = {
    "export_ban": "export_control",
    "local_processing_requirement": "local_processing",
    "royalty_tax": "tax_royalty",
    "foreign_investment_review": "investment_restriction",
    "environmental_protection": "environment_policy",
}

RISK_SCORE_BY_POLICY_TYPE = {
    "export_control": 0.90,
    "local_processing": 0.80,
    "state_control": 0.75,
    "investment_restriction": 0.70,
    "environment_policy": 0.65,
    "tax_royalty": 0.60,
    "permitting": 0.55,
    "strategic_plan": 0.45,
    "recycling": 0.35,
    "subsidy_support": 0.25,
    "unknown": 0.40,
}


def read_csv_safely(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()


def load_data():
    for path in INPUT_CANDIDATES:
        if not path.exists():
            continue
        df = read_csv_safely(path)
        if not df.empty:
            return df, path.name
    return pd.DataFrame(), ""


def normalize_country(value):
    country = str(value or "").strip()
    aliases = {
        "People's Republic of China": "China",
        "Democratic Republic of the Congo": "Democratic Republic of Congo",
        "DRC": "Democratic Republic of Congo",
        "Plurinational State of Bolivia": "Bolivia",
        "USA": "United States",
        "United States of America": "United States",
    }
    return aliases.get(country, country)


def load_project_countries():
    if not PROJECT_COUNTRY_PATH.exists():
        return set()
    project_df = read_csv_safely(PROJECT_COUNTRY_PATH)
    if project_df.empty or "country" not in project_df.columns:
        return set()
    return {
        normalize_country(country)
        for country in project_df["country"].dropna().astype(str)
        if str(country).strip()
    }


def combine_text(row):
    fields = [
        "policy_name",
        "title",
        "name",
        "description",
        "summary_cn",
        "mineral_scope",
        "mineral",
        "policy_type",
        "policy_subtype",
        "stage",
        "affected_stage",
        "catl_risk_dimension",
        "source_name",
    ]
    return " ".join(str(row.get(field, "")) for field in fields).lower()


def is_lithium_related_policy(row):
    text = combine_text(row)
    has_lithium = any(keyword in text for keyword in LITHIUM_KEYWORDS)
    if has_lithium:
        return True

    has_non_lithium = any(keyword in text for keyword in NON_LITHIUM_MINERALS)
    if has_non_lithium:
        return False

    return False


def is_project_country_policy(row, project_countries):
    if not project_countries:
        return False

    country = normalize_country(row.get("country", ""))
    if country not in project_countries:
        return False

    policy_type = normalize_policy_type(row.get("policy_type", "unknown"))
    mineral_scope = str(row.get("mineral_scope", "")).lower()
    relevance_score = pd.to_numeric(
        pd.Series([row.get("relevance_score", 0)]),
        errors="coerce",
    ).fillna(0).iloc[0]

    if any(keyword in combine_text(row) for keyword in LITHIUM_KEYWORDS):
        return True

    if policy_type in {
        "export_control",
        "local_processing",
        "state_control",
        "tax_royalty",
        "environment_policy",
        "investment_restriction",
        "permitting",
    }:
        return True

    if mineral_scope in {"critical_minerals", "battery_minerals", "general_mining"}:
        return True

    return relevance_score >= 0.55


def normalize_policy_type(value):
    policy_type = str(value or "unknown").strip()
    return POLICY_TYPE_MAP.get(policy_type, policy_type if policy_type else "unknown")


def ensure_risk_score(df):
    df = df.copy()
    if "policy_type" not in df.columns:
        df["policy_type"] = "unknown"
    df["policy_type"] = df["policy_type"].apply(normalize_policy_type)

    if "risk_score" in df.columns:
        risk_score = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0)
    else:
        risk_score = pd.Series(0, index=df.index, dtype=float)

    needs_score = risk_score.max() <= 0
    if needs_score:
        risk_score = df["policy_type"].map(RISK_SCORE_BY_POLICY_TYPE).fillna(0.40)

    df["risk_score"] = risk_score.clip(0, 1)
    return df


def base_shock(policy_type):
    mapping = {
        "export_control": 0.25,
        "local_processing": 0.18,
        "state_control": 0.12,
        "tax_royalty": 0.10,
        "environment_policy": 0.08,
        "investment_restriction": 0.10,
        "permitting": 0.06,
        "strategic_plan": 0.03,
        "recycling": 0.02,
        "subsidy_support": -0.02,
    }
    return mapping.get(policy_type, 0.03)


def intensity(score):
    if score >= 0.85:
        return 1.30
    if score >= 0.70:
        return 1.15
    if score >= 0.55:
        return 1.00
    if score >= 0.40:
        return 0.60
    return 0.30


def compute_components(df):
    if df.empty:
        return df

    df = df.copy()
    df = ensure_risk_score(df)

    if "policy_id" not in df.columns:
        df["policy_id"] = [f"lithium_policy_{idx}" for idx in range(len(df))]
    if "country" not in df.columns:
        df["country"] = ""
    df["country"] = df["country"].apply(normalize_country)
    if "policy_name" not in df.columns:
        for candidate in ["title", "name"]:
            if candidate in df.columns:
                df["policy_name"] = df[candidate]
                break
        if "policy_name" not in df.columns:
            df["policy_name"] = ""

    df["policy_base_impact"] = df["policy_type"].apply(base_shock)
    df["policy_intensity"] = df["risk_score"].apply(intensity)
    df["policy_risk_premium_pct"] = df["policy_base_impact"] * df["policy_intensity"]

    df["export_pressure"] = df["policy_type"].eq("export_control").astype(float) * df["risk_score"]
    df["processing_pressure"] = df["policy_type"].eq("local_processing").astype(float) * df["risk_score"]
    df["fiscal_pressure"] = df["policy_type"].eq("tax_royalty").astype(float) * df["risk_score"]
    df["delay_pressure"] = (
        df["policy_type"].isin(["permitting", "environment_policy"]).astype(float)
        * df["risk_score"]
    )
    df["last_updated"] = str(date.today())

    output_columns = REQUIRED_OUTPUT_COLUMNS.copy()
    if "source_url" in df.columns:
        output_columns.append("source_url")

    return df[output_columns]


def main():
    raw_df, source_name = load_data()

    if raw_df.empty:
        pd.DataFrame(columns=REQUIRED_OUTPUT_COLUMNS).to_csv(
            OUTPUT_PATH,
            index=False,
            encoding="utf-8-sig",
        )
        print("source file: none")
        print("raw policy rows: 0")
        print("lithium policy rows: 0")
        print("output rows: 0")
        print("saved:", OUTPUT_PATH)
        return

    project_countries = load_project_countries()
    lithium_mask = raw_df.apply(is_lithium_related_policy, axis=1)
    project_country_mask = raw_df.apply(
        lambda row: is_project_country_policy(row, project_countries),
        axis=1,
    )
    lithium_df = raw_df[lithium_mask | project_country_mask].copy()
    out = compute_components(lithium_df)
    out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("source file:", source_name)
    print("raw policy rows:", len(raw_df))
    print("project countries:", len(project_countries))
    print("lithium policy rows:", len(lithium_df))
    print("direct lithium policy rows:", int(lithium_mask.sum()))
    print("project-country policy rows:", int(project_country_mask.sum()))
    print("output rows:", len(out))
    print("saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
