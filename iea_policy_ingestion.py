from pathlib import Path
import json
import re
from datetime import datetime

import pandas as pd


REPORTS_DIR = Path("reports")

RAW_POLICY_PATH = REPORTS_DIR / "iea_critical_minerals_policies_raw.csv"
TRACKER_OUTPUT_PATH = REPORTS_DIR / "critical_minerals_policy_tracker.csv"
ALERTS_OUTPUT_PATH = REPORTS_DIR / "critical_minerals_policy_alerts.csv"

TRACKER_COLUMNS = [
    "policy_id",
    "country",
    "region",
    "mineral",
    "policy_name",
    "policy_type",
    "policy_year",
    "effective_date",
    "status",
    "risk_level",
    "risk_direction",
    "affected_stage",
    "catl_impact_dimension",
    "relevance_score",
    "risk_score",
    "summary_cn",
    "source",
    "source_url",
    "last_updated",
]

ALERT_COLUMNS = [
    "alert_id",
    "country",
    "policy_name",
    "policy_type",
    "effective_date",
    "risk_level",
    "affected_stage",
    "catl_impact_dimension",
    "alert_summary_cn",
    "management_implication_cn",
    "source_url",
    "sort_score",
]


def load_raw_policy_data():
    if not RAW_POLICY_PATH.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(RAW_POLICY_PATH, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def combine_text(row):
    fields = [
        "policy_name",
        "title",
        "description",
        "policy_area",
        "policy_type_raw",
        "policyType",
        "mineral",
        "source",
    ]
    values = []
    for field in fields:
        value = row.get(field, "")
        if pd.isna(value):
            value = ""
        values.append(str(value))
    return " ".join(values).lower()


def _contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def classify_policy_type(row):
    text = combine_text(row)

    if _contains_any(text, ["export ban", "export control", "export restriction", "ban on export", "restrict exports"]):
        return "export_ban"
    if _contains_any(text, ["beneficiation", "local processing", "value addition", "domestic processing", "refining facility", "processing requirement"]):
        return "local_processing_requirement"
    if _contains_any(text, ["national lithium strategy", "state participation", "state-owned", "government majority", "strategic control", "national company"]):
        return "state_control"
    if _contains_any(text, ["protected area", "salt flat protection", "environmental permit", "water", "biodiversity", "environmental protection"]):
        return "environmental_protection"
    if _contains_any(text, ["royalty", "tax", "levy", "mining tax", "fiscal regime"]):
        return "royalty_tax"
    if _contains_any(text, ["foreign investment", "ownership restriction", "investment screening", "national security review"]):
        return "foreign_investment_review"
    if _contains_any(text, ["loan facility", "subsidy", "grant", "tax credit", "support program", "production credit"]):
        return "subsidy_support"
    if _contains_any(text, ["strategy", "roadmap", "critical minerals strategy", "action plan"]):
        return "strategic_plan"
    if _contains_any(text, ["permit", "license", "approval", "concession"]):
        return "permitting"
    if _contains_any(text, ["recycling", "circular economy", "secondary materials"]):
        return "recycling"

    return "unknown"


def classify_affected_stage(row):
    text = combine_text(row)

    if _contains_any(text, ["raw ore", "ore export", "unprocessed ore", "crushed ore"]):
        return "ore_export"
    if _contains_any(text, ["concentrate", "lithium concentrate", "spodumene concentrate"]):
        return "concentrate_export"
    if _contains_any(text, ["beneficiation", "local processing", "domestic processing", "value addition"]):
        return "processing"
    if _contains_any(text, ["lithium sulphate", "lithium carbonate", "hydroxide", "refining", "conversion"]):
        return "refining"
    if _contains_any(text, ["permit", "concession", "license", "approval"]):
        return "project_approval"
    if _contains_any(text, ["state participation", "government majority", "national company", "state-owned"]):
        return "contract_structure"
    if _contains_any(text, ["loan", "subsidy", "grant", "tax credit", "support program"]):
        return "financing"
    if _contains_any(text, ["protected area", "salt flat", "water", "environmental review", "biodiversity"]):
        return "environmental_permitting"
    if _contains_any(text, ["foreign investment", "ownership restriction", "screening"]):
        return "investment_access"

    return "general_policy"


def classify_risk_direction(policy_type):
    if policy_type in [
        "export_ban",
        "local_processing_requirement",
        "state_control",
        "foreign_investment_review",
        "royalty_tax",
        "environmental_protection",
        "permitting",
    ]:
        return "restrictive"

    if policy_type in [
        "subsidy_support",
        "recycling",
        "strategic_plan",
    ]:
        return "supportive"

    return "neutral"


def map_region(country):
    if country == "Australia":
        return "Oceania"
    if country in ["Chile", "Argentina", "Brazil", "Bolivia", "Peru"]:
        return "South America"
    if country in [
        "Zimbabwe",
        "Namibia",
        "Tanzania",
        "Democratic Republic of Congo",
        "South Africa",
    ]:
        return "Africa"
    if country in ["Canada", "United States"]:
        return "North America"
    if country in ["China", "People's Republic of China", "Indonesia"]:
        return "Asia"
    return "Other"


def classify_catl_impact(row):
    policy_type = row.get("policy_type", "")
    return {
        "export_ban": "resource_security",
        "local_processing_requirement": "investment_access;project_schedule",
        "state_control": "investment_access;valuation_impact",
        "environmental_protection": "project_schedule;policy_compliance",
        "royalty_tax": "procurement_cost;valuation_impact",
        "foreign_investment_review": "investment_access",
        "subsidy_support": "supply_stability",
        "permitting": "project_schedule",
    }.get(policy_type, "policy_compliance")


def _primary_country(row):
    raw_value = row.get("country", row.get("countries", ""))
    if pd.isna(raw_value):
        return ""

    raw_text = str(raw_value).strip()
    if not raw_text:
        return ""

    try:
        countries = json.loads(raw_text)
        if isinstance(countries, list) and countries:
            first_country = countries[0]
            if isinstance(first_country, dict):
                return str(first_country.get("name", "") or "")
    except Exception:
        pass

    return raw_text


def _source_url(row):
    value = row.get("source_url", row.get("learnMore", ""))
    if pd.isna(value):
        return ""
    return str(value)


def _policy_name(row):
    value = row.get("policy_name", row.get("title", ""))
    if pd.isna(value):
        return ""
    return str(value)


def _policy_year(row):
    value = row.get("policy_year", row.get("year", ""))
    year_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(year_value):
        return ""
    return int(year_value)


def _effective_date(row):
    for field in ["effective_date", "datePromulgated", "year"]:
        value = row.get(field, "")
        if pd.isna(value):
            continue
        value_text = str(value).strip()
        if value_text:
            return value_text
    return ""


def _mineral(row):
    text = combine_text(row)
    if _contains_any(text, ["lithium", "spodumene", "brine", "lithium concentrate"]):
        return "Lithium"
    if "nickel" in text:
        return "Nickel"
    if "cobalt" in text:
        return "Cobalt"
    if "graphite" in text:
        return "Graphite"
    if "copper" in text:
        return "Copper"
    if "manganese" in text:
        return "Manganese"
    if "rare earth" in text:
        return "Rare earth"
    return "Critical minerals"


def _policy_id(row, index):
    country = re.sub(r"[^a-z0-9]+", "_", _primary_country(row).lower()).strip("_")
    name = re.sub(r"[^a-z0-9]+", "_", _policy_name(row).lower()).strip("_")
    year = _policy_year(row) or "unknown"
    if not country:
        country = "unknown_country"
    if not name:
        name = "unknown_policy"
    return f"iea_{country}_{year}_{name}"[:180] + f"_{index}"


def calculate_relevance_score(row):
    text = combine_text(row)
    score = 0.35

    if _contains_any(text, ["lithium", "spodumene", "brine", "lithium concentrate"]):
        score = max(score, 0.90)
    elif "battery minerals" in text:
        score = max(score, 0.80)
    elif "critical minerals" in text:
        score = max(score, 0.70)
    elif _contains_any(text, ["mining", "mineral processing", "raw materials"]):
        score = max(score, 0.55)

    if _primary_country(row) in [
        "Australia",
        "Chile",
        "Argentina",
        "Zimbabwe",
        "Namibia",
        "Tanzania",
        "Canada",
        "China",
        "People's Republic of China",
        "United States",
        "Brazil",
        "Bolivia",
        "Peru",
        "Democratic Republic of Congo",
        "Indonesia",
    ]:
        score += 0.05

    return min(max(score, 0), 1)


def calculate_risk_score(row):
    policy_type = row.get("policy_type", classify_policy_type(row))
    affected_stage = row.get("affected_stage", classify_affected_stage(row))
    risk_direction = row.get("risk_direction", classify_risk_direction(policy_type))
    text = combine_text(row)

    score = {
        "export_ban": 0.90,
        "local_processing_requirement": 0.80,
        "state_control": 0.75,
        "foreign_investment_review": 0.70,
        "environmental_protection": 0.65,
        "royalty_tax": 0.60,
        "permitting": 0.55,
        "strategic_plan": 0.45,
        "recycling": 0.35,
        "subsidy_support": 0.25,
        "unknown": 0.40,
    }.get(policy_type, 0.40)

    if affected_stage in ["ore_export", "concentrate_export"]:
        score += 0.10
    if "lithium" in text:
        score += 0.08
    if _primary_country(row) in [
        "Australia",
        "Chile",
        "Argentina",
        "Zimbabwe",
        "Namibia",
        "Tanzania",
        "Canada",
        "China",
        "People's Republic of China",
        "United States",
        "Brazil",
        "Bolivia",
        "Peru",
        "Democratic Republic of Congo",
        "Indonesia",
    ]:
        score += 0.05
    if policy_type == "export_ban" and affected_stage == "concentrate_export":
        score += 0.05
    if policy_type == "subsidy_support":
        score -= 0.10
    if risk_direction == "supportive":
        score -= 0.15

    return min(max(score, 0), 1)


def map_risk_level(score):
    if score >= 0.85:
        return "极高"
    if score >= 0.70:
        return "高"
    if score >= 0.55:
        return "中高"
    if score >= 0.40:
        return "中"
    return "低"


def make_summary_cn(row):
    country = row.get("country", "")
    policy_type = row.get("policy_type", "")

    if policy_type == "export_ban":
        return f"{country} 政策涉及出口限制，可能影响锂矿/关键矿产跨境供应弹性。"
    if policy_type == "local_processing_requirement":
        return f"{country} 政策强化本地加工或增值要求，可能提高项目资本开支与建设复杂度。"
    if policy_type == "state_control":
        return f"{country} 政策提高国家参与度或战略控制，可能影响项目权益结构与投资准入。"
    if policy_type == "environmental_protection":
        return f"{country} 政策强化环保或许可要求，可能影响项目审批节奏和可开发资源范围。"
    if policy_type == "subsidy_support":
        return f"{country} 政策提供产业支持，可能提升本地供应稳定性并降低低价周期停产风险。"
    return f"{country} 关键矿产政策可能影响资源投资、供应稳定或项目执行条件。"


def normalize_policy_data(raw_df):
    if raw_df.empty:
        return pd.DataFrame(columns=TRACKER_COLUMNS)

    records = []
    last_updated = datetime.now().strftime("%Y-%m-%d")

    for index, (_, raw_row) in enumerate(raw_df.iterrows(), start=1):
        normalized_row = raw_row.to_dict()
        country = _primary_country(normalized_row)
        policy_type = classify_policy_type(normalized_row)
        affected_stage = classify_affected_stage(normalized_row)
        risk_direction = classify_risk_direction(policy_type)

        normalized_row.update(
            {
                "country": country,
                "policy_type": policy_type,
                "affected_stage": affected_stage,
                "risk_direction": risk_direction,
            }
        )
        relevance_score = calculate_relevance_score(normalized_row)
        if relevance_score < 0.50:
            continue

        risk_score = calculate_risk_score(normalized_row)
        normalized_row["risk_score"] = risk_score

        records.append(
            {
                "policy_id": _policy_id(normalized_row, index),
                "country": country,
                "region": map_region(country),
                "mineral": _mineral(normalized_row),
                "policy_name": _policy_name(normalized_row),
                "policy_type": policy_type,
                "policy_year": _policy_year(normalized_row),
                "effective_date": _effective_date(normalized_row),
                "status": str(normalized_row.get("status", "") or ""),
                "risk_level": map_risk_level(risk_score),
                "risk_direction": risk_direction,
                "affected_stage": affected_stage,
                "catl_impact_dimension": classify_catl_impact(normalized_row),
                "relevance_score": round(relevance_score, 2),
                "risk_score": round(risk_score, 2),
                "summary_cn": make_summary_cn(normalized_row),
                "source": str(normalized_row.get("source", "") or ""),
                "source_url": _source_url(normalized_row),
                "last_updated": last_updated,
            }
        )

    return pd.DataFrame(records, columns=TRACKER_COLUMNS)


def make_management_implication(row):
    policy_type = row.get("policy_type", "")

    if policy_type == "export_ban":
        return "建议复核该国矿石或精矿出口假设，并评估替代资源与本地加工要求。"
    if policy_type == "local_processing_requirement":
        return "建议将当地选矿、转化加工、能源、用水和审批能力纳入项目准入条件。"
    if policy_type == "state_control":
        return "建议重新评估权益结构、政府参与比例和合同稳定性。"
    if policy_type == "environmental_protection":
        return "建议跟踪环保许可、盐湖保护和社区约束对项目进度的影响。"
    if policy_type == "subsidy_support":
        return "该政策可能提升资源供给稳定性，可作为低风险资源配置的支持因素。"

    return "建议纳入资源国风险评分，并持续跟踪政策落地情况。"


def generate_policy_alerts(tracker_df):
    if tracker_df.empty:
        return pd.DataFrame(columns=ALERT_COLUMNS)

    alert_df = tracker_df.copy()
    alert_df["relevance_score_num"] = pd.to_numeric(
        alert_df.get("relevance_score", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0)
    alert_df["risk_score_num"] = pd.to_numeric(
        alert_df.get("risk_score", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0)

    alert_df = alert_df[
        alert_df.get("risk_level", pd.Series(dtype=str)).isin(["极高", "高", "中高"])
        & (alert_df["relevance_score_num"] >= 0.60)
    ].copy()

    if alert_df.empty:
        return pd.DataFrame(columns=ALERT_COLUMNS)

    alert_df["sort_score"] = (
        alert_df["risk_score_num"] * 0.7
        + alert_df["relevance_score_num"] * 0.3
    ).round(3)
    alert_df = alert_df.sort_values("sort_score", ascending=False).head(20).copy()

    output_df = pd.DataFrame(
        {
            "alert_id": "alert_" + alert_df["policy_id"].astype(str),
            "country": alert_df.get("country", ""),
            "policy_name": alert_df.get("policy_name", ""),
            "policy_type": alert_df.get("policy_type", ""),
            "effective_date": alert_df.get("effective_date", ""),
            "risk_level": alert_df.get("risk_level", ""),
            "affected_stage": alert_df.get("affected_stage", ""),
            "catl_impact_dimension": alert_df.get("catl_impact_dimension", ""),
            "alert_summary_cn": alert_df.get("summary_cn", ""),
            "management_implication_cn": alert_df.apply(make_management_implication, axis=1),
            "source_url": alert_df.get("source_url", ""),
            "sort_score": alert_df["sort_score"],
        }
    )

    return output_df[ALERT_COLUMNS]


def empty_output_files():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=TRACKER_COLUMNS).to_csv(
        TRACKER_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(columns=ALERT_COLUMNS).to_csv(
        ALERTS_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )


def main():
    input_exists = RAW_POLICY_PATH.exists()
    raw_df = load_raw_policy_data()
    input_rows = len(raw_df)
    tracker_df = pd.DataFrame(columns=TRACKER_COLUMNS)
    alerts_df = pd.DataFrame(columns=ALERT_COLUMNS)

    if raw_df.empty:
        empty_output_files()
    else:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        tracker_df = normalize_policy_data(raw_df)
        alerts_df = generate_policy_alerts(tracker_df)
        tracker_df.to_csv(
            TRACKER_OUTPUT_PATH,
            index=False,
            encoding="utf-8-sig",
        )
        alerts_df.to_csv(
            ALERTS_OUTPUT_PATH,
            index=False,
            encoding="utf-8-sig",
        )

    print(f"?????{input_rows}")
    print(f"tracker?????{len(tracker_df)}")
    print(f"alerts?????{len(alerts_df)}")
    print(f"tracker?????{TRACKER_OUTPUT_PATH}")
    print(f"alerts?????{ALERTS_OUTPUT_PATH}")
    if alerts_df.empty:
        print("?5?alerts??")
    else:
        print("?5?alerts?")
        print(alerts_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
