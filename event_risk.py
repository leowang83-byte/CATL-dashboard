import pandas as pd

from database import load_table


COUNTRY_KEYWORDS = {
    "Australia": ["australia", "greenbushes", "pilbara", "pilgangoora"],
    "Chile": ["chile", "atacama", "salar"],
    "Argentina": ["argentina", "salta", "catamarca", "jujuy"],
    "Zimbabwe": ["zimbabwe", "bikita", "sandawana"],
    "Mali": ["mali", "goulamina"],
    "China": ["china", "jiangxi", "yichun"],
}


def detect_country_from_title(title):
    title_lower = str(title or "").lower()

    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return country

    return None


def build_country_event_risk():
    """
    从 event_data 中提取国家层面的新闻风险。
    输出：
    - country
    - event_risk_score
    - event_count
    - negative_event_count
    - latest_event_title
    """
    try:
        events = load_table("event_data")
    except Exception:
        return pd.DataFrame(
            columns=[
                "country",
                "event_risk_score",
                "event_count",
                "negative_event_count",
                "latest_event_title",
            ]
        )

    if events.empty:
        return pd.DataFrame(
            columns=[
                "country",
                "event_risk_score",
                "event_count",
                "negative_event_count",
                "latest_event_title",
            ]
        )

    events["detected_country"] = events["title"].apply(detect_country_from_title)
    events = events.dropna(subset=["detected_country"]).copy()

    if events.empty:
        return pd.DataFrame(
            columns=[
                "country",
                "event_risk_score",
                "event_count",
                "negative_event_count",
                "latest_event_title",
            ]
        )

    events["risk_score"] = events["risk_score"].fillna(0.1)
    events["impact_direction"] = events["impact_direction"].fillna("neutral")

    output_rows = []

    for country, group in events.groupby("detected_country"):
        group_sorted = group.sort_values("created_at", ascending=False)

        event_risk_score = group["risk_score"].max()
        event_count = len(group)
        negative_event_count = len(group[group["impact_direction"] == "negative"])
        latest_event_title = group_sorted["title"].iloc[0]

        output_rows.append(
            {
                "country": country,
                "event_risk_score": round(float(event_risk_score), 3),
                "event_count": int(event_count),
                "negative_event_count": int(negative_event_count),
                "latest_event_title": latest_event_title,
            }
        )

    return pd.DataFrame(output_rows)