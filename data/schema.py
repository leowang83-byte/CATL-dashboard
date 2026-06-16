import pandas as pd


def enforce_schema(df):
    df = df.copy()

    if "project_name" not in df.columns:
        if "name" in df.columns:
            df["project_name"] = df["name"]
        elif "project" in df.columns:
            df["project_name"] = df["project"]

    if "lce_capacity" not in df.columns:
        if "effective_capacity" in df.columns:
            df["lce_capacity"] = df["effective_capacity"]
        elif "annual_capacity" in df.columns:
            df["lce_capacity"] = df["annual_capacity"]

    defaults = {
        "project_name": "N/A",
        "lce_capacity": 0,
        "adjusted_aisc": 0,
        "policy_risk_score": 0,
    }
    for k, v in defaults.items():
        if k not in df.columns:
            df[k] = v

    for col in ["lce_capacity", "adjusted_aisc", "policy_risk_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(defaults[col])

    df["project_name"] = df["project_name"].fillna(defaults["project_name"]).astype(str)
    return df
