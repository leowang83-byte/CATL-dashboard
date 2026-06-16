from datetime import date
from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")
INPUT_PATH = REPORTS_DIR / "policy_master_table.csv"
SCORED_OUTPUT_PATH = REPORTS_DIR / "policy_scored_table.csv"
TIMELINE_OUTPUT_PATH = REPORTS_DIR / "policy_timeline_events.csv"

SCORED_COLUMNS = [
    "policy_id",
    "policy_name",
    "country",
    "region",
    "policy_type",
    "policy_subtype",
    "mineral_scope",
    "stage",
    "policy_strength",
    "time_start",
    "time_end",
    "risk_score",
    "impact_score",
    "relevance_score",
    "catl_exposure_score",
    "timeline_weight",
    "risk_level",
    "timeline_lane",
    "timeline_year",
    "is_stock_constraint",
    "is_future_constraint",
    "catl_risk_dimension",
    "risk_direction",
    "source_system",
    "source_name",
    "source_url",
    "data_quality_score",
    "last_updated",
]

TIMELINE_COLUMNS = [
    "event_id",
    "policy_id",
    "country",
    "policy_name",
    "timeline_year",
    "timeline_lane",
    "policy_type",
    "policy_subtype",
    "risk_level",
    "risk_score",
    "impact_score",
    "relevance_score",
    "timeline_weight",
    "is_stock_constraint",
    "is_future_constraint",
    "catl_risk_dimension",
    "risk_direction",
    "summary_label",
    "hover_text",
    "source_url",
]

CATL_FOCUS_COUNTRIES = {
    "Australia",
    "Chile",
    "Argentina",
    "Zimbabwe",
    "Namibia",
    "Tanzania",
    "Canada",
    "China",
    "United States",
    "Brazil",
    "Bolivia",
    "Peru",
    "Democratic Republic of Congo",
    "Indonesia",
}


def safe_float(value, default=0.0):
    if value is None or pd.isna(value):
        return default

    try:
        text = str(value).strip().replace(",", "")
        if not text:
            return default
        return float(text)
    except Exception:
        return default


def _clamp_score(value):
    return max(0.0, min(1.0, value))


def calculate_risk_score(row):
    original_score = safe_float(row.get("risk_score", 0), 0)
    if original_score > 0:
        return _clamp_score(original_score)

    policy_type = str(row.get("policy_type", "")).strip()
    stage = str(row.get("stage", "")).strip()
    mineral_scope = str(row.get("mineral_scope", "")).strip()
    policy_strength = str(row.get("policy_strength", "")).strip()
    risk_direction = str(row.get("risk_direction", "")).strip()
    country = str(row.get("country", "")).strip()
    time_start = int(safe_float(row.get("time_start", 0), 0))

    base_scores = {
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

    score = base_scores.get(policy_type, 0.40)

    if stage in {"ore_export", "concentrate_export"}:
        score += 0.10
    if mineral_scope in {"lithium", "spodumene", "brine"}:
        score += 0.08
    if policy_strength == "hard_constraint":
        score += 0.08
    if 2027 <= time_start <= 2030:
        score += 0.05
    if country in CATL_FOCUS_COUNTRIES:
        score += 0.05
    if policy_type == "subsidy_support":
        score -= 0.10
    if risk_direction == "supportive":
        score -= 0.15

    return _clamp_score(score)


def calculate_catl_exposure_score(row):
    country = str(row.get("country", "")).strip()
    mineral_scope = str(row.get("mineral_scope", "")).strip()
    stage = str(row.get("stage", "")).strip()
    policy_type = str(row.get("policy_type", "")).strip()

    score = 0.80 if country in CATL_FOCUS_COUNTRIES else 0.40

    if mineral_scope in {"lithium", "spodumene", "brine"}:
        score += 0.10
    if stage in {"ore_export", "concentrate_export", "processing", "refining"}:
        score += 0.05
    if policy_type in {"export_control", "local_processing", "state_control"}:
        score += 0.05

    return _clamp_score(score)


def calculate_timeline_weight(row):
    risk_score = safe_float(row.get("risk_score", 0), 0)
    impact_score = safe_float(row.get("impact_score", 0.40), 0.40)
    relevance_score = safe_float(row.get("relevance_score", 0.50), 0.50)
    catl_exposure_score = safe_float(row.get("catl_exposure_score", 0), 0)

    weight = (
        risk_score * 0.45
        + impact_score * 0.25
        + relevance_score * 0.20
        + catl_exposure_score * 0.10
    )
    return _clamp_score(weight)


def map_risk_level(score):
    score = safe_float(score, 0)
    if score >= 0.85:
        return "\u6781\u9ad8"
    if score >= 0.70:
        return "\u9ad8"
    if score >= 0.55:
        return "\u4e2d\u9ad8"
    if score >= 0.40:
        return "\u4e2d"
    return "\u4f4e"


def map_timeline_lane(policy_type):
    lane_map = {
        "export_control": "\u51fa\u53e3\u9650\u5236\u4e0e\u672c\u5730\u52a0\u5de5",
        "local_processing": "\u51fa\u53e3\u9650\u5236\u4e0e\u672c\u5730\u52a0\u5de5",
        "state_control": "\u56fd\u5bb6\u63a7\u80a1\u4e0e\u56fd\u5bb6\u53c2\u4e0e",
        "tax_royalty": "\u7a0e\u8d39\u6743\u5229\u91d1\u4e0e\u8bb8\u53ef\u7ea6\u675f",
        "permitting": "\u7a0e\u8d39\u6743\u5229\u91d1\u4e0e\u8bb8\u53ef\u7ea6\u675f",
        "investment_restriction": "\u7a0e\u8d39\u6743\u5229\u91d1\u4e0e\u8bb8\u53ef\u7ea6\u675f",
        "environment_policy": "\u73af\u4fdd\u4fdd\u62a4\u4e0e\u6c34\u8d44\u6e90\u7ea6\u675f",
        "subsidy_support": "\u653f\u7b56\u652f\u6301\u4e0e\u4f9b\u5e94\u7a33\u5b9a",
        "strategic_plan": "\u6218\u7565\u89c4\u5212\u4e0e\u4ea7\u4e1a\u652f\u6301",
        "recycling": "\u56de\u6536\u4e0e\u5faa\u73af\u4f53\u7cfb",
        "unknown": "\u5176\u4ed6\u653f\u7b56\u7ea6\u675f",
    }
    return lane_map.get(str(policy_type).strip(), lane_map["unknown"])


def map_timeline_year(time_start):
    year = int(safe_float(time_start, 0))
    if year <= 0:
        return 2025, False, False
    if year <= 2024:
        return 2025, True, False
    if 2025 <= year <= 2035:
        return year, False, year >= 2027
    return 2035, False, True


def make_summary_label(row):
    country = str(row.get("country", "")).strip() or "Unknown"
    policy_type = str(row.get("policy_type", "")).strip() or "unknown"
    risk_level = str(row.get("risk_level", "")).strip() or "\u672a\u8bc4\u7ea7"
    return f"{country}\uff5c{policy_type}\uff5c{risk_level}"


def make_hover_text(row):
    return (
        f"\u56fd\u5bb6\uff1a{row.get('country', '')}<br>"
        f"\u653f\u7b56\u540d\u79f0\uff1a{row.get('policy_name', '')}<br>"
        f"\u653f\u7b56\u7c7b\u578b\uff1a{row.get('policy_type', '')}<br>"
        f"\u751f\u6548\u5e74\u4efd\uff1a{row.get('timeline_year', '')}<br>"
        f"\u98ce\u9669\u7b49\u7ea7\uff1a{row.get('risk_level', '')}<br>"
        f"\u98ce\u9669\u5206\u6570\uff1a{safe_float(row.get('risk_score', 0), 0):.2f}<br>"
        f"\u5f71\u54cd\u7ef4\u5ea6\uff1a{row.get('catl_risk_dimension', '')}<br>"
        f"\u6765\u6e90\uff1a{row.get('source_url', '')}"
    )


def score_policy_master(master_df):
    if master_df.empty:
        return pd.DataFrame(columns=SCORED_COLUMNS)

    scored_df = master_df.copy()
    for column in SCORED_COLUMNS:
        if column not in scored_df.columns:
            scored_df[column] = ""

    scored_df["impact_score"] = scored_df["impact_score"].apply(
        lambda value: safe_float(value, 0.40)
    )
    scored_df["relevance_score"] = scored_df["relevance_score"].apply(
        lambda value: safe_float(value, 0.50)
    )
    scored_df["risk_score"] = scored_df.apply(calculate_risk_score, axis=1).round(3)
    scored_df["catl_exposure_score"] = scored_df.apply(
        calculate_catl_exposure_score,
        axis=1,
    ).round(3)
    scored_df["timeline_weight"] = scored_df.apply(
        calculate_timeline_weight,
        axis=1,
    ).round(3)
    scored_df["risk_level"] = scored_df["risk_score"].apply(map_risk_level)

    return scored_df[SCORED_COLUMNS]


def generate_timeline_events(scored_df):
    if scored_df.empty:
        return pd.DataFrame(columns=TIMELINE_COLUMNS)

    rows = []
    for _, row in scored_df.iterrows():
        policy_id = str(row.get("policy_id", "")).strip()
        policy_name = str(row.get("policy_name", "")).strip()
        if not policy_id and not policy_name:
            continue

        timeline_year, is_stock_constraint, is_future_constraint = map_timeline_year(
            row.get("time_start", "")
        )
        timeline_year = max(2025, min(2035, int(timeline_year)))
        event_policy_id = policy_id or policy_name

        event = {
            "event_id": f"timeline_{event_policy_id}",
            "policy_id": policy_id,
            "country": row.get("country", ""),
            "policy_name": policy_name,
            "timeline_year": timeline_year,
            "timeline_lane": map_timeline_lane(row.get("policy_type", "")),
            "policy_type": row.get("policy_type", ""),
            "policy_subtype": row.get("policy_subtype", ""),
            "risk_level": row.get("risk_level", ""),
            "risk_score": safe_float(row.get("risk_score", 0), 0),
            "impact_score": safe_float(row.get("impact_score", 0), 0),
            "relevance_score": safe_float(row.get("relevance_score", 0), 0),
            "timeline_weight": safe_float(row.get("timeline_weight", 0), 0),
            "is_stock_constraint": is_stock_constraint,
            "is_future_constraint": is_future_constraint,
            "catl_risk_dimension": row.get("catl_risk_dimension", ""),
            "risk_direction": row.get("risk_direction", ""),
            "source_url": row.get("source_url", ""),
        }
        event["summary_label"] = make_summary_label(event)
        event["hover_text"] = make_hover_text(event)
        rows.append(event)

    timeline_df = pd.DataFrame(rows, columns=TIMELINE_COLUMNS)
    if timeline_df.empty:
        return timeline_df

    timeline_df = timeline_df.sort_values(
        by=["timeline_year", "timeline_weight"],
        ascending=[True, False],
    ).reset_index(drop=True)
    return timeline_df[TIMELINE_COLUMNS]


def load_policy_master():
    if not INPUT_PATH.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()


def write_empty_outputs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=SCORED_COLUMNS).to_csv(
        SCORED_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(columns=TIMELINE_COLUMNS).to_csv(
        TIMELINE_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )


def main():
    master_df = load_policy_master()

    if master_df.empty:
        write_empty_outputs()
        print("No policy_master_table.csv data found. Empty outputs generated.")
        print("Input rows: 0")
        print(f"scored output: {SCORED_OUTPUT_PATH}")
        print(f"timeline output: {TIMELINE_OUTPUT_PATH}")
        print(f"run date: {date.today().isoformat()}")
        return

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    scored_df = score_policy_master(master_df)
    timeline_df = generate_timeline_events(scored_df)

    scored_df.to_csv(
        SCORED_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )
    timeline_df.to_csv(
        TIMELINE_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Input rows: {len(master_df)}")
    print(f"scored rows: {len(scored_df)}")
    print("risk_level distribution:")
    print(scored_df["risk_level"].value_counts(dropna=False).to_string())
    print(f"risk_score mean: {scored_df['risk_score'].mean():.3f}")
    print(f"timeline_weight mean: {scored_df['timeline_weight'].mean():.3f}")
    print(f"timeline rows: {len(timeline_df)}")
    print("timeline_year distribution:")
    print(timeline_df["timeline_year"].value_counts().sort_index().to_string())
    print("timeline_lane distribution:")
    print(timeline_df["timeline_lane"].value_counts().to_string())
    print(f"scored output: {SCORED_OUTPUT_PATH}")
    print(f"timeline output: {TIMELINE_OUTPUT_PATH}")
    print(f"run date: {date.today().isoformat()}")


if __name__ == "__main__":
    main()
