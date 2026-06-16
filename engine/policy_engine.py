import pandas as pd


def compute_policy_signal(df):
    df = df.copy()
    df["policy_tier"] = pd.cut(
        df["policy_risk_score"],
        bins=[0, 0.4, 0.7, 1.0],
        labels=["low", "mid", "high"],
        include_lowest=True,
    )
    return df
