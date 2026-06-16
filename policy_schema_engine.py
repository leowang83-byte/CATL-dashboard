from datetime import date
from pathlib import Path
import json
import re

import pandas as pd


REPORTS_DIR = Path("reports")

TRACKER_PATH = REPORTS_DIR / "critical_minerals_policy_tracker.csv"
IEA_RAW_PATH = REPORTS_DIR / "iea_critical_minerals_policies_raw.csv"
IEA_FULL_PATH = REPORTS_DIR / "iea_policies_raw_full.csv"
IEA_SUPPLEMENT_PATH = REPORTS_DIR / "iea_policy_supplement.csv"
OUTPUT_PATH = REPORTS_DIR / "policy_master_table.csv"

POLICY_MASTER_COLUMNS = [
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
    "catl_risk_dimension",
    "risk_direction",
    "source_system",
    "source_name",
    "source_url",
    "data_quality_score",
    "last_updated",
]


def get_value(row, candidates, default=""):
    for candidate in candidates:
        if candidate not in row:
            continue

        value = row.get(candidate)
        if pd.isna(value):
            continue

        value_text = str(value).strip()
        if value_text:
            return value

    return default


def combine_text(row):
    fields = [
        "policy_name",
        "title",
        "name",
        "description",
        "summary_cn",
        "policy_area",
        "policy_type_raw",
        "policy_type",
        "policy_subtype",
        "mineral",
        "mineral_scope",
        "affected_stage",
        "stage",
        "catl_impact_dimension",
    ]
    values = []
    for field in fields:
        if field not in row:
            continue

        value = row.get(field)
        if pd.isna(value):
            continue

        value_text = str(value).strip()
        if value_text:
            values.append(value_text)

    return " ".join(values).lower()


def classify_policy_type(row):
    old_policy_type = str(get_value(row, ["policy_type"], "")).strip()
    old_mapping = {
        "export_ban": "export_control",
        "local_processing_requirement": "local_processing",
        "state_control": "state_control",
        "royalty_tax": "tax_royalty",
        "foreign_investment_review": "investment_restriction",
        "environmental_protection": "environment_policy",
        "subsidy_support": "subsidy_support",
        "strategic_plan": "strategic_plan",
        "permitting": "permitting",
        "recycling": "recycling",
    }
    if old_policy_type in old_mapping:
        return old_mapping[old_policy_type]

    text = combine_text(row)
    keyword_rules = [
        (
            "export_control",
            [
                "export ban",
                "export control",
                "export restriction",
                "ban on export",
                "restrict exports",
            ],
        ),
        (
            "local_processing",
            [
                "beneficiation",
                "local processing",
                "value addition",
                "domestic processing",
                "refining facility",
                "processing requirement",
            ],
        ),
        (
            "state_control",
            [
                "national lithium strategy",
                "state participation",
                "state-owned",
                "government majority",
                "strategic control",
                "national company",
            ],
        ),
        (
            "tax_royalty",
            [
                "royalty",
                "tax",
                "levy",
                "mining tax",
                "fiscal regime",
            ],
        ),
        (
            "environment_policy",
            [
                "protected area",
                "salt flat protection",
                "environmental permit",
                "water",
                "biodiversity",
                "environmental protection",
            ],
        ),
        (
            "investment_restriction",
            [
                "foreign investment",
                "ownership restriction",
                "investment screening",
                "national security review",
            ],
        ),
        (
            "subsidy_support",
            [
                "loan facility",
                "subsidy",
                "grant",
                "tax credit",
                "support program",
                "production credit",
            ],
        ),
        (
            "strategic_plan",
            [
                "strategy",
                "roadmap",
                "critical minerals strategy",
                "action plan",
            ],
        ),
        (
            "permitting",
            [
                "permit",
                "license",
                "approval",
                "concession",
            ],
        ),
        (
            "recycling",
            [
                "recycling",
                "circular economy",
                "secondary materials",
            ],
        ),
    ]

    for policy_type, keywords in keyword_rules:
        if any(keyword in text for keyword in keywords):
            return policy_type

    return "unknown"


def classify_policy_subtype(row):
    text = combine_text(row)
    policy_type = str(get_value(row, ["policy_type"], "")).strip()
    if policy_type in [
        "export_ban",
        "local_processing_requirement",
        "state_control",
        "royalty_tax",
        "foreign_investment_review",
        "environmental_protection",
        "subsidy_support",
        "strategic_plan",
        "permitting",
        "recycling",
    ]:
        policy_type = classify_policy_type(row)

    if "raw ore" in text or "unprocessed ore" in text:
        return "export_ban_raw_ore"
    if "concentrate" in text or "lithium concentrate" in text or "spodumene concentrate" in text:
        return "export_ban_concentrate"
    if policy_type == "export_control":
        return "export_control_general"
    if "beneficiation" in text:
        return "local_beneficiation"
    if "domestic processing" in text or "local processing" in text or "value addition" in text:
        return "domestic_processing"
    if "national lithium strategy" in text:
        return "lithium_strategy"
    if "state participation" in text:
        return "state_participation"
    if "state-owned" in text or "national company" in text:
        return "state_owned_mandate"
    if "royalty" in text:
        return "royalty_increase"
    if "tax" in text:
        return "tax_change"
    if "protected area" in text:
        return "environmental_protection_zone"
    if "salt flat" in text:
        return "salt_flat_protection"
    if "foreign investment" in text or "screening" in text:
        return "foreign_investment_screening"
    if "permit" in text or "license" in text or "concession" in text:
        return "project_license"
    if "loan facility" in text:
        return "loan_facility"
    if "critical minerals strategy" in text:
        return "critical_minerals_strategy"
    if "recycling" in text:
        return "recycling_support"

    return "unknown"


def classify_mineral_scope(row):
    text = combine_text(row)
    multi_mineral_terms = [
        "cobalt",
        "nickel",
        "graphite",
        "rare earth",
        "copper",
        "manganese",
    ]
    multi_mineral_count = sum(term in text for term in multi_mineral_terms)

    if "spodumene" in text:
        return "spodumene"
    if "brine" in text or "salt lake" in text or "salar" in text:
        return "brine"
    if "lithium" in text:
        return "lithium"
    if "battery minerals" in text or "battery metals" in text:
        return "battery_minerals"
    if "critical minerals" in text:
        return "critical_minerals"
    if multi_mineral_count >= 2:
        return "multi_mineral"
    if "mining" in text or "mineral processing" in text or "raw materials" in text:
        return "general_mining"

    return "unknown"


def classify_stage(row):
    old_stage = str(get_value(row, ["stage", "affected_stage"], "")).strip()
    old_mapping = {
        "ore_export": "ore_export",
        "concentrate_export": "concentrate_export",
        "processing": "processing",
        "refining": "refining",
        "project_approval": "project_approval",
        "contract_structure": "investment_access",
        "financing": "financing",
        "environmental_permitting": "environmental_permitting",
        "investment_access": "investment_access",
    }
    if old_stage in old_mapping:
        return old_mapping[old_stage]

    text = combine_text(row)
    if (
        "raw ore" in text
        or "ore export" in text
        or "unprocessed ore" in text
        or "crushed ore" in text
    ):
        return "ore_export"
    if "concentrate" in text or "lithium concentrate" in text or "spodumene concentrate" in text:
        return "concentrate_export"
    if (
        "beneficiation" in text
        or "local processing" in text
        or "domestic processing" in text
        or "value addition" in text
    ):
        return "processing"
    if (
        "lithium sulphate" in text
        or "lithium carbonate" in text
        or "hydroxide" in text
        or "refining" in text
        or "conversion" in text
    ):
        return "refining"
    if "permit" in text or "concession" in text or "license" in text or "approval" in text:
        return "project_approval"
    if (
        "state participation" in text
        or "government majority" in text
        or "national company" in text
        or "foreign investment" in text
        or "ownership restriction" in text
        or "screening" in text
    ):
        return "investment_access"
    if "loan" in text or "subsidy" in text or "grant" in text or "tax credit" in text or "support program" in text:
        return "financing"
    if (
        "protected area" in text
        or "salt flat" in text
        or "water" in text
        or "environmental review" in text
        or "biodiversity" in text
    ):
        return "environmental_permitting"
    if "recycling" in text or "circular economy" in text:
        return "recycling"

    return "general_policy"


def classify_policy_strength(policy_type, policy_subtype, text):
    text = str(text or "").lower()

    if policy_type == "export_control" or any(
        keyword in text
        for keyword in [
            "ban",
            "prohibition",
            "mandatory",
            "required",
        ]
    ):
        return "hard_constraint"

    if policy_type in [
        "local_processing",
        "state_control",
        "tax_royalty",
        "investment_restriction",
        "environment_policy",
        "permitting",
    ]:
        return "medium_constraint"

    if policy_type in [
        "strategic_plan",
        "recycling",
    ]:
        return "soft_policy"

    if policy_type == "subsidy_support":
        return "support_policy"

    return "unknown"


def classify_risk_direction(policy_type):
    if policy_type in [
        "export_control",
        "local_processing",
        "state_control",
        "tax_royalty",
        "environment_policy",
        "investment_restriction",
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
    if country in ["China", "Indonesia"]:
        return "Asia"
    if country in [
        "European Union",
        "Germany",
        "France",
        "United Kingdom",
        "Portugal",
        "Spain",
        "Finland",
        "Sweden",
    ]:
        return "Europe"
    return "Other"


def classify_catl_risk_dimension(policy_type):
    return {
        "export_control": "resource_security",
        "local_processing": "investment_access;project_schedule",
        "state_control": "investment_access;valuation_impact",
        "tax_royalty": "procurement_cost;valuation_impact",
        "environment_policy": "project_schedule;policy_compliance",
        "investment_restriction": "investment_access",
        "subsidy_support": "supply_stability",
        "permitting": "project_schedule",
        "recycling": "supply_stability",
        "strategic_plan": "policy_compliance",
        "unknown": "policy_compliance",
    }.get(policy_type, "policy_compliance")


def calculate_impact_score(policy_strength):
    return {
        "hard_constraint": 0.90,
        "medium_constraint": 0.70,
        "soft_policy": 0.45,
        "support_policy": 0.35,
        "unknown": 0.40,
    }.get(policy_strength, 0.40)


def calculate_relevance_score_from_mineral(mineral_scope):
    return {
        "lithium": 0.90,
        "spodumene": 0.90,
        "brine": 0.90,
        "battery_minerals": 0.80,
        "critical_minerals": 0.70,
        "multi_mineral": 0.65,
        "general_mining": 0.55,
        "unknown": 0.35,
    }.get(mineral_scope, 0.35)


def calculate_data_quality_score(row):
    score = 0.50

    if str(get_value(row, ["country"], "")).strip():
        score += 0.10
    if str(get_value(row, ["policy_name"], "")).strip():
        score += 0.10
    if str(get_value(row, ["source_url"], "")).strip():
        score += 0.10
    if str(get_value(row, ["time_start"], "")).strip():
        score += 0.10
    if str(get_value(row, ["policy_type"], "unknown")).strip() != "unknown":
        score += 0.10

    return min(score, 1.00)


def extract_year(value):
    if pd.isna(value):
        return ""

    match = re.search(r"\b(\d{4})\b", str(value))
    if not match:
        return ""

    return match.group(1)


def build_policy_id(country, policy_name, time_start):
    base_text = f"{country}_{policy_name}_{time_start}".lower()
    slug = re.sub(r"[^a-z0-9]+", "_", base_text)
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = "unknown"
    return f"policy_{slug}"[:120]


def extract_countries(row):
    direct_country = str(get_value(row, ["country", "jurisdiction", "geography"], "")).strip()
    countries_raw = get_value(row, ["countries"], "")
    countries = []

    if countries_raw is not None and str(countries_raw).strip():
        try:
            parsed = json.loads(str(countries_raw))
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        country_name = str(item.get("name", "")).strip()
                        if country_name:
                            countries.append(country_name)
        except Exception:
            pass

    if not countries and direct_country:
        countries = [direct_country]

    cleaned = []
    for country in countries:
        if country not in cleaned:
            cleaned.append(country)
    return cleaned


def load_best_available_policy_data():
    input_paths = [
        IEA_RAW_PATH,
        TRACKER_PATH,
        IEA_FULL_PATH,
    ]

    for input_path in input_paths:
        if not input_path.exists():
            continue

        try:
            df = pd.read_csv(input_path, encoding="utf-8-sig")
        except Exception:
            continue

        if not df.empty:
            if IEA_SUPPLEMENT_PATH.exists():
                try:
                    supplement_df = pd.read_csv(IEA_SUPPLEMENT_PATH, encoding="utf-8-sig")
                except Exception:
                    supplement_df = pd.DataFrame()
                if not supplement_df.empty:
                    df = pd.concat([df, supplement_df], ignore_index=True, sort=False)
            return df, input_path.name

    return pd.DataFrame(), ""


def normalize_to_policy_master(raw_df, source_file_name):
    if raw_df.empty:
        return pd.DataFrame(columns=POLICY_MASTER_COLUMNS)

    records = []
    last_updated = date.today().isoformat()
    source_file_lower = str(source_file_name or "").lower()

    for _, raw_row in raw_df.iterrows():
        row = raw_row.to_dict()
        policy_name = str(get_value(row, ["policy_name", "title", "name"], "")).strip()
        countries = extract_countries(row)
        policy_type = classify_policy_type(row)
        policy_subtype = classify_policy_subtype(row)
        mineral_scope = classify_mineral_scope(row)
        stage = classify_stage(row)
        text = combine_text(row)
        policy_strength = classify_policy_strength(policy_type, policy_subtype, text)

        time_start_raw = get_value(
            row,
            ["policy_year", "effective_date", "start_year", "year"],
            "",
        )
        time_start = extract_year(time_start_raw)
        time_end_raw = get_value(row, ["time_end", "end_year", "expiry_year"], "")
        time_end = extract_year(time_end_raw)

        original_policy_id = str(get_value(row, ["policy_id", "id"], "")).strip()

        original_risk_score = get_value(row, ["risk_score"], "")
        risk_score = "" if str(original_risk_score).strip() == "" else original_risk_score
        impact_score = calculate_impact_score(policy_strength)
        original_relevance_score = get_value(row, ["relevance_score"], "")
        relevance_score = (
            calculate_relevance_score_from_mineral(mineral_scope)
            if str(original_relevance_score).strip() == ""
            else original_relevance_score
        )
        catl_risk_dimension = classify_catl_risk_dimension(policy_type)
        risk_direction = classify_risk_direction(policy_type)

        if "iea" in source_file_lower:
            source_system = "IEA"
        else:
            source_system = "unknown"

        if "critical_minerals_policy_tracker" in source_file_lower:
            source_name = "IEA Critical Minerals Policy Tracker"
        elif "iea" in source_file_lower:
            source_name = "IEA Policies Database"
        else:
            source_name = "unknown"

        source_url = str(get_value(row, ["source_url", "url", "link", "learnMore"], "")).strip()
        if not source_url:
            source_url = "https://www.iea.org/data-and-statistics/data-tools/critical-minerals-policy-tracker"

        for country in countries:
            region = str(get_value(row, ["region"], "")).strip() or map_region(country)
            policy_id = (
                f"{original_policy_id}_{build_policy_id(country, policy_name, time_start)}"
                if original_policy_id
                else build_policy_id(country, policy_name, time_start)
            )

            quality_row = {
                **row,
                "country": country,
                "policy_name": policy_name,
                "source_url": source_url,
                "time_start": time_start,
                "policy_type": policy_type,
            }

            records.append(
                {
                    "policy_id": policy_id,
                    "policy_name": policy_name,
                    "country": country,
                    "region": region,
                    "policy_type": policy_type,
                    "policy_subtype": policy_subtype,
                    "mineral_scope": mineral_scope,
                    "stage": stage,
                    "policy_strength": policy_strength,
                    "time_start": time_start,
                    "time_end": time_end,
                    "risk_score": risk_score,
                    "impact_score": impact_score,
                    "relevance_score": relevance_score,
                    "catl_risk_dimension": catl_risk_dimension,
                    "risk_direction": risk_direction,
                    "source_system": source_system,
                    "source_name": source_name,
                    "source_url": source_url,
                    "data_quality_score": calculate_data_quality_score(quality_row),
                    "last_updated": last_updated,
                }
            )

    return pd.DataFrame(records, columns=POLICY_MASTER_COLUMNS)


def write_empty_policy_master():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=POLICY_MASTER_COLUMNS).to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )


def main():
    policy_df, source_file = load_best_available_policy_data()

    if policy_df.empty:
        write_empty_policy_master()
        master_df = pd.DataFrame(columns=POLICY_MASTER_COLUMNS)
    else:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        master_df = normalize_to_policy_master(policy_df, source_file)
        master_df.to_csv(
            OUTPUT_PATH,
            index=False,
            encoding="utf-8-sig",
        )

    print(f"?????????{source_file}")
    print(f"?????{len(policy_df)}")
    print(f"?????{len(master_df)}")
    print(f"?????{OUTPUT_PATH}")
    print("policy_type???")
    if master_df.empty or "policy_type" not in master_df.columns:
        print("?")
    else:
        print(master_df["policy_type"].value_counts(dropna=False).to_string())
    print("mineral_scope???")
    if master_df.empty or "mineral_scope" not in master_df.columns:
        print("?")
    else:
        print(master_df["mineral_scope"].value_counts(dropna=False).to_string())
    quality_mean = pd.to_numeric(
        master_df.get("data_quality_score", pd.Series(dtype=float)),
        errors="coerce",
    ).mean()
    if pd.isna(quality_mean):
        print("data_quality_score????0.00")
    else:
        print(f"data_quality_score????{quality_mean:.2f}")


if __name__ == "__main__":
    main()
