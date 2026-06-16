def compute_risk_adjusted_aisc(df):
    df = df.copy()
    df["risk_adjusted_aisc"] = df["adjusted_aisc"] * (1 + df["policy_risk_score"] * 0.2)
    return df
