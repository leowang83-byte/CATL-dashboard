from datetime import date

import pandas as pd

from database import get_connection, load_table


COUNTRY_KEYWORDS = {
    "Australia": ["australia", "greenbushes", "pilbara", "pilgangoora", "wodgina"],
    "Chile": ["chile", "atacama", "maricunga"],
    "Argentina": ["argentina", "salta", "catamarca", "jujuy", "olaroz", "cauchari"],
    "Zimbabwe": ["zimbabwe", "bikita", "arcadia", "zulu"],
    "Mali": ["mali", "goulamina"],
    "Ghana": ["ghana", "ewoyaa"],
    "Brazil": ["brazil", "sigma", "grota do cirilo"],
    "Canada": ["canada", "quebec", "james bay", "whabouchi"],
    "United States": ["united states", "u.s.", "us ", "thacker pass", "silver peak"],
    "China": ["china", "jiangxi", "yichun"],
    "Democratic Republic of Congo": ["congo", "drc", "manono"],
    "Portugal": ["portugal", "barroso"],
    "Germany": ["germany", "zinnwald"],
    "Czech Republic": ["czech", "cinovec"],
}


POLICY_RULES = [
    {
        "policy_type": "raw_ore_export_ban",
        "keywords": [
            "export ban",
            "ban exports",
            "bans export",
            "raw ore export",
            "ore export ban",
            "lithium ore export ban",
            "ban on lithium exports",
            "ban on lithium ore exports",
        ],
        "supply_shock": 0.80,
        "cost_shock": 0.15,
        "delay_months": 12,
        "confidence": 0.90,
    },
    {
        "policy_type": "export_restriction",
        "keywords": [
            "export restriction",
            "export restrictions",
            "restrict exports",
            "export permit",
            "export license",
        ],
        "supply_shock": 0.60,
        "cost_shock": 0.10,
        "delay_months": 9,
        "confidence": 0.80,
    },
    {
        "policy_type": "local_processing_requirement",
        "keywords": [
            "local processing",
            "local beneficiation",
            "domestic processing",
            "in-country processing",
            "value addition",
            "local processing requirement",
        ],
        "supply_shock": 0.40,
        "cost_shock": 0.20,
        "delay_months": 18,
        "confidence": 0.80,
    },
    {
        "policy_type": "royalty_or_tax_hike",
        "keywords": [
            "royalty",
            "tax hike",
            "higher tax",
            "mining tax",
            "windfall tax",
        ],
        "supply_shock": 0.10,
        "cost_shock": 0.15,
        "delay_months": 3,
        "confidence": 0.70,
    },
    {
        "policy_type": "foreign_ownership_limit",
        "keywords": [
            "foreign ownership",
            "ownership limit",
            "nationalization",
            "state ownership",
        ],
        "supply_shock": 0.20,
        "cost_shock": 0.05,
        "delay_months": 12,
        "confidence": 0.70,
    },
    {
        "policy_type": "environmental_approval_delay",
        "keywords": [
            "environmental approval",
            "permit delay",
            "licence delay",
            "license delay",
            "environmental review",
        ],
        "supply_shock": 0.30,
        "cost_shock": 0.10,
        "delay_months": 12,
        "confidence": 0.70,
    },
    {
        "policy_type": "logistics_or_port_restriction",
        "keywords": [
            "port restriction",
            "transport disruption",
            "rail disruption",
            "road blockade",
            "logistics disruption",
        ],
        "supply_shock": 0.30,
        "cost_shock": 0.10,
        "delay_months": 3,
        "confidence": 0.65,
    },
]


def normalize_text(text):
    return str(text or "").lower()


def detect_country(title):
    title_lower = normalize_text(title)

    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return country

    return None


def detect_policy_event(title):
    title_lower = normalize_text(title)

    for rule in POLICY_RULES:
        for keyword in rule["keywords"]:
            if keyword in title_lower:
                return rule

    return None


def ensure_policy_events_table():
    sql = """
    CREATE TABLE IF NOT EXISTS policy_events (
        id SERIAL PRIMARY KEY,
        country TEXT,
        project_name TEXT,
        event_date DATE DEFAULT CURRENT_DATE,
        policy_type TEXT,
        event_title TEXT,
        supply_shock FLOAT,
        cost_shock FLOAT,
        delay_months INT,
        affected_lce_tonnes FLOAT,
        confidence FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def policy_event_exists(country, policy_type, event_title):
    sql = """
    SELECT id
    FROM policy_events
    WHERE country = %s
      AND policy_type = %s
      AND event_title = %s
    LIMIT 1;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (country, policy_type, event_title))
            return cur.fetchone() is not None


def insert_policy_event(event):
    if policy_event_exists(
        event["country"],
        event["policy_type"],
        event["event_title"],
    ):
        return False

    sql = """
    INSERT INTO policy_events (
        country,
        project_name,
        event_date,
        policy_type,
        event_title,
        supply_shock,
        cost_shock,
        delay_months,
        affected_lce_tonnes,
        confidence
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    event["country"],
                    event.get("project_name", ""),
                    event.get("event_date", date.today()),
                    event["policy_type"],
                    event["event_title"],
                    event["supply_shock"],
                    event["cost_shock"],
                    event["delay_months"],
                    event["affected_lce_tonnes"],
                    event["confidence"],
                ),
            )
        conn.commit()

    return True


def infer_affected_lce_tonnes(country, supply_shock):
    try:
        mines = load_table("mining_projects")
    except Exception:
        return 0.0

    if mines.empty:
        return 0.0

    if "country" not in mines.columns or "annual_capacity" not in mines.columns:
        return 0.0

    country_mines = mines[mines["country"] == country].copy()

    if country_mines.empty:
        return 0.0

    country_mines["annual_capacity"] = pd.to_numeric(
        country_mines["annual_capacity"],
        errors="coerce"
    ).fillna(0)

    total_capacity = country_mines["annual_capacity"].sum()

    return float(total_capacity * supply_shock)


def generate_policy_events_from_news():
    ensure_policy_events_table()

    try:
        events = load_table("event_data")
    except Exception:
        print("event_data not found. Run news_pipeline.py first.")
        return pd.DataFrame()

    if events.empty:
        print("No news events found.")
        return pd.DataFrame()

    generated_events = []

    for _, row in events.iterrows():
        title = row.get("title", "")

        country = detect_country(title)
        rule = detect_policy_event(title)

        if not country or not rule:
            continue

        affected_lce_tonnes = infer_affected_lce_tonnes(
            country=country,
            supply_shock=rule["supply_shock"],
        )

        event = {
            "country": country,
            "project_name": "",
            "event_date": date.today(),
            "policy_type": rule["policy_type"],
            "event_title": title,
            "supply_shock": rule["supply_shock"],
            "cost_shock": rule["cost_shock"],
            "delay_months": rule["delay_months"],
            "affected_lce_tonnes": affected_lce_tonnes,
            "confidence": rule["confidence"],
        }

        inserted = insert_policy_event(event)

        if inserted:
            generated_events.append(event)

    output = pd.DataFrame(generated_events)

    print(f"Generated new policy events: {len(output)}")

    return output


def build_country_policy_shock():
    try:
        policy_events = load_table("policy_events")
    except Exception:
        return pd.DataFrame(
            columns=[
                "country",
                "policy_supply_shock",
                "policy_cost_shock",
                "policy_delay_months",
                "affected_lce_tonnes",
            ]
        )

    if policy_events.empty:
        return pd.DataFrame(
            columns=[
                "country",
                "policy_supply_shock",
                "policy_cost_shock",
                "policy_delay_months",
                "affected_lce_tonnes",
            ]
        )

    required_cols = [
        "country",
        "supply_shock",
        "cost_shock",
        "delay_months",
        "affected_lce_tonnes",
    ]

    for col in required_cols:
        if col not in policy_events.columns:
            policy_events[col] = 0

    policy_events["country"] = policy_events["country"].fillna("")
    policy_events["supply_shock"] = pd.to_numeric(
        policy_events["supply_shock"],
        errors="coerce"
    ).fillna(0)
    policy_events["cost_shock"] = pd.to_numeric(
        policy_events["cost_shock"],
        errors="coerce"
    ).fillna(0)
    policy_events["delay_months"] = pd.to_numeric(
        policy_events["delay_months"],
        errors="coerce"
    ).fillna(0)
    policy_events["affected_lce_tonnes"] = pd.to_numeric(
        policy_events["affected_lce_tonnes"],
        errors="coerce"
    ).fillna(0)

    policy_events = policy_events[policy_events["country"] != ""].copy()

    if policy_events.empty:
        return pd.DataFrame(
            columns=[
                "country",
                "policy_supply_shock",
                "policy_cost_shock",
                "policy_delay_months",
                "affected_lce_tonnes",
            ]
        )

    output = (
        policy_events
        .groupby("country")
        .agg(
            policy_supply_shock=("supply_shock", "max"),
            policy_cost_shock=("cost_shock", "max"),
            policy_delay_months=("delay_months", "max"),
            affected_lce_tonnes=("affected_lce_tonnes", "sum"),
        )
        .reset_index()
    )

    return output


def apply_policy_shock_to_resource_table(resource_cost_table):
    country_policy = build_country_policy_shock()

    df = resource_cost_table.copy()

    policy_cols = [
        "policy_supply_shock",
        "policy_cost_shock",
        "policy_delay_months",
        "affected_lce_tonnes",
    ]

    for col in policy_cols:
        if col in df.columns:
            df = df.drop(columns=[col])

    if not country_policy.empty and "country" in country_policy.columns:
        df = df.merge(country_policy, on="country", how="left")

    for col in policy_cols:
        if col not in df.columns:
            df[col] = 0

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "annual_capacity" in df.columns:
        df["annual_capacity"] = pd.to_numeric(
            df["annual_capacity"],
            errors="coerce"
        ).fillna(0)

        df["effective_capacity"] = (
            df["annual_capacity"] * (1 - df["policy_supply_shock"])
        )
    else:
        df["effective_capacity"] = 0

    if "realtime_aisc" not in df.columns:
        df["realtime_aisc"] = 0

    df["realtime_aisc"] = pd.to_numeric(
        df["realtime_aisc"],
        errors="coerce"
    ).fillna(0)

    df["policy_compliance_cost"] = (
        df["realtime_aisc"] * df["policy_cost_shock"]
    )

    df["adjusted_aisc"] = (
        df["realtime_aisc"] + df["policy_compliance_cost"]
    )

    if "energy_cost" not in df.columns:
        df["energy_cost"] = 0

    if "transport_cost" not in df.columns:
        df["transport_cost"] = 0

    df["energy_cost"] = pd.to_numeric(
        df["energy_cost"],
        errors="coerce"
    ).fillna(0)

    df["transport_cost"] = pd.to_numeric(
        df["transport_cost"],
        errors="coerce"
    ).fillna(0)

    df["delivered_cost"] = (
        df["adjusted_aisc"]
        + df["energy_cost"]
        + df["transport_cost"]
    )

    return df


def estimate_policy_price_impact(resource_cost_table, base_price_center):
    df = resource_cost_table.copy()

    if "annual_capacity" in df.columns:
        total_capacity = pd.to_numeric(
            df["annual_capacity"],
            errors="coerce"
        ).fillna(0).sum()
    else:
        total_capacity = 0

    if "effective_capacity" in df.columns:
        total_effective_capacity = pd.to_numeric(
            df["effective_capacity"],
            errors="coerce"
        ).fillna(0).sum()
    else:
        total_effective_capacity = total_capacity

    if total_capacity > 0:
        supply_loss_ratio = max(
            0,
            (total_capacity - total_effective_capacity) / total_capacity,
        )
    else:
        supply_loss_ratio = 0

    if "realtime_aisc" in df.columns and "adjusted_aisc" in df.columns:
        base_aisc_90 = pd.to_numeric(
            df["realtime_aisc"],
            errors="coerce"
        ).fillna(0).quantile(0.9)

        adjusted_aisc_90 = pd.to_numeric(
            df["adjusted_aisc"],
            errors="coerce"
        ).fillna(0).quantile(0.9)

        aisc_uplift = max(0, adjusted_aisc_90 - base_aisc_90)
    else:
        aisc_uplift = 0

    supply_premium = base_price_center * supply_loss_ratio * 0.6
    aisc_premium = aisc_uplift * 0.4

    expected_lce_price = base_price_center + supply_premium + aisc_premium

    return {
        "base_price_center": round(float(base_price_center), 2),
        "supply_loss_ratio": round(float(supply_loss_ratio), 4),
        "aisc_uplift": round(float(aisc_uplift), 2),
        "supply_premium": round(float(supply_premium), 2),
        "aisc_premium": round(float(aisc_premium), 2),
        "expected_lce_price": round(float(expected_lce_price), 2),
    }


if __name__ == "__main__":
    generate_policy_events_from_news()
    summary = build_country_policy_shock()
    print(summary)