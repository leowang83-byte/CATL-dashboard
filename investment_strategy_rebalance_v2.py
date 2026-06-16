from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")
INPUT = REPORTS_DIR / "project_strategic_aisc_v2.csv"
OLD_INPUT = REPORTS_DIR / "investment_recommendations.csv"
OUTPUT = REPORTS_DIR / "investment_recommendations_v2.csv"
CURRENT_LCE_PRICE_WAN = 18.20

OUTPUT_COLUMNS = [
    "rank",
    "project",
    "project_name",
    "company",
    "country",
    "resource_type",
    "status",
    "annual_capacity",
    "effective_capacity",
    "base_aisc_wan",
    "adjusted_aisc_wan",
    "strategic_aisc_wan",
    "strategy_base_aisc_wan",
    "policy_risk_premium_wan",
    "policy_risk_premium_pct",
    "adjusted_minus_base_wan",
    "strategic_minus_adjusted_wan",
    "current_lce_price_wan",
    "price_margin_wan",
    "price_margin_pct",
    "strategic_aisc_percentile",
    "policy_premium_flag",
    "capacity_score",
    "cost_score",
    "margin_score",
    "policy_risk_score_norm",
    "strategic_investment_score",
    "score_percentile",
    "investment_tier",
    "recommended_action_v2",
    "strategy_detail_v2",
    "key_risk_note",
]

NUMERIC_COLUMNS = [
    "base_aisc_wan",
    "adjusted_aisc_wan",
    "strategic_aisc_wan",
    "strategy_base_aisc_wan",
    "policy_risk_premium_wan",
    "policy_risk_premium_pct",
    "adjusted_minus_base_wan",
    "strategic_minus_adjusted_wan",
    "annual_capacity",
    "effective_capacity",
    "risk_score",
    "policy_risk_score",
    "event_risk_score",
]


def load_dataframe(path):
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def load_inputs():
    main_df = load_dataframe(INPUT)
    old_df = load_dataframe(OLD_INPUT)
    return main_df, old_df


def safe_numeric(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def clean_text(value, default=""):
    if pd.isna(value) or value is None:
        return default
    text = str(value).strip()
    return text if text else default


def pick_first(row, candidates, default=""):
    for col in candidates:
        if col in row.index:
            value = row.get(col)
            text = clean_text(value, "")
            if text:
                return text
    return default


def pick_capacity(df):
    candidates = [
        "effective_capacity",
        "annual_capacity",
        "capacity_lce",
        "annual_capacity_lce",
        "capacity",
    ]
    for col in candidates:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce").fillna(0)
            if float(series.max()) > 0:
                return col
    return None


def margin_bucket(price_margin_wan):
    if price_margin_wan < 0:
        return 20.0
    if price_margin_wan < 1:
        return 40.0
    if price_margin_wan < 3:
        return 55.0
    if price_margin_wan < 5:
        return 70.0
    if price_margin_wan < 8:
        return 85.0
    return 100.0


def clamp_text(text, limit=80):
    text = clean_text(text, "")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def assign_tier(row):
    margin_wan = float(row.get("price_margin_wan", 0) or 0)
    score_percentile = float(row.get("score_percentile", 0) or 0)
    if margin_wan < 0:
        return "Tier 4｜价格倒挂"
    if score_percentile >= 0.90:
        return "Tier 1｜优先锁定"
    if score_percentile >= 0.70:
        return "Tier 2｜重点跟踪"
    if score_percentile >= 0.40:
        return "Tier 3｜观察储备"
    return "Tier 4｜暂缓推进"


def build_strategy_detail(row):
    parts = []
    if float(row.get("strategic_aisc_wan", 0) or 0) > 0:
        if float(row.get("price_margin_wan", 0) or 0) >= 0:
            parts.append("战略AISC低于当前LCE价格，具备价格安全垫。")
        else:
            parts.append("战略AISC高于当前LCE价格，当前价格下经济性承压。")

    if bool(row.get("policy_premium_flag", False)):
        parts.append("存在政策/战略风险溢价，需重点跟踪资源国政策、审批和本地加工要求。")

    if float(row.get("capacity_score", 0) or 0) >= 70:
        parts.append("项目产能贡献较高，对资源配置具有战略意义。")

    if float(row.get("cost_score", 0) or 0) >= 70:
        parts.append("项目处于样本库低成本区间。")

    if not parts:
        parts.append("继续跟踪成本、政策与项目执行节奏。")

    return clamp_text(" ".join(parts), 80)


def build_risk_note(row):
    if bool(row.get("policy_premium_flag", False)):
        return "政策风险已进入战略AISC，关注出口限制、本地加工、审批、税费或环保约束。"
    if float(row.get("price_margin_wan", 0) or 0) < 0:
        return "战略AISC高于当前价格，价格倒挂风险。"
    if float(row.get("adjusted_minus_base_wan", 0) or 0) >= 1.0:
        return "运营调整幅度较大，关注能源、运输、爬坡或物流成本。"
    return "暂无显著额外风险，继续跟踪项目进展。"


def default_action(tier):
    if tier == "Tier 1｜优先锁定":
        return "优先锁定 / 股权投资候选"
    if tier == "Tier 2｜重点跟踪":
        return "重点跟踪 / 长协或期权式布局"
    if tier == "Tier 3｜观察储备":
        return "观察储备 / 等待成本或政策改善"
    if tier == "Tier 4｜价格倒挂":
        return "暂缓投资 / 价格倒挂风险"
    return "暂缓推进 / 保留信息跟踪"


def compute_scores(df):
    df = df.copy()
    df = safe_numeric(df, NUMERIC_COLUMNS)

    df["strategy_base_aisc_wan"] = df[["base_aisc_wan", "adjusted_aisc_wan"]].max(axis=1)
    df["current_lce_price_wan"] = CURRENT_LCE_PRICE_WAN
    df["price_margin_wan"] = CURRENT_LCE_PRICE_WAN - df["strategic_aisc_wan"]
    df["price_margin_pct"] = 0.0

    valid_mask = df["strategic_aisc_wan"] > 0
    df.loc[valid_mask, "price_margin_pct"] = (
        df.loc[valid_mask, "price_margin_wan"] / df.loc[valid_mask, "strategic_aisc_wan"]
    )

    if len(df) > 0:
        df["strategic_aisc_percentile"] = (
            df["strategic_aisc_wan"].rank(method="average", pct=True)
        )
    else:
        df["strategic_aisc_percentile"] = 0.0

    df["policy_premium_flag"] = df["policy_risk_premium_wan"] > 0

    capacity_col = pick_capacity(df)
    if capacity_col is None:
        df["capacity_score"] = 50.0
    else:
        max_capacity = float(df[capacity_col].max())
        if max_capacity <= 0:
            df["capacity_score"] = 50.0
        else:
            df["capacity_score"] = (df[capacity_col] / max_capacity * 100).clip(0, 100)

    df["cost_score"] = ((1 - df["strategic_aisc_percentile"]) * 100).clip(0, 100)
    df["margin_score"] = df["price_margin_wan"].apply(margin_bucket)
    df["policy_risk_score_norm"] = df[
        ["policy_risk_score", "risk_score", "event_risk_score"]
    ].max(axis=1).clip(0, 1)

    policy_score_component = (1 - df["policy_risk_score_norm"]) * 100
    df["strategic_investment_score"] = (
        df["cost_score"] * 0.35
        + df["margin_score"] * 0.30
        + df["capacity_score"] * 0.20
        + policy_score_component * 0.15
    ).round(2)
    if len(df) > 0:
        score_rank = df["strategic_investment_score"].rank(method="first")
        df["score_percentile"] = (score_rank / (len(df) + 1)).round(4)
    else:
        df["score_percentile"] = 0.0

    return df


def build_legacy_lookup(old_df):
    lookup = {}
    if old_df.empty:
        return lookup
    for _, row in old_df.iterrows():
        key = (
            clean_text(row.get("name", row.get("project", ""))),
            clean_text(row.get("country", "")),
            clean_text(row.get("resource_type", "")),
        )
        lookup[key] = {
            "recommended_action": clean_text(row.get("recommended_action", "")),
            "strategy_detail": clean_text(row.get("strategy_detail", "")),
            "investment_score": row.get("investment_score", ""),
        }
    return lookup


def build_recommendations(df):
    df = df.copy()
    df = safe_numeric(df, NUMERIC_COLUMNS)

    if "project" not in df.columns:
        df["project"] = df.apply(
            lambda row: pick_first(row, ["project", "name"], default=""),
            axis=1,
        )
    else:
        df["project"] = df["project"].apply(lambda x: clean_text(x, ""))
        if "name" in df.columns:
            df["project"] = df["project"].where(df["project"] != "", df["name"].astype(str))

    if "project_name" not in df.columns:
        df["project_name"] = df.apply(
            lambda row: pick_first(row, ["project_name", "project", "name"], default=""),
            axis=1,
        )
    else:
        df["project_name"] = df["project_name"].apply(lambda x: clean_text(x, ""))
        df["project_name"] = df["project_name"].where(df["project_name"] != "", df["project"])

    if "company" not in df.columns:
        df["company"] = df.apply(
            lambda row: pick_first(row, ["company", "owner"], default=""),
            axis=1,
        )
    else:
        df["company"] = df["company"].apply(lambda x: clean_text(x, ""))
        if "owner" in df.columns:
            owner_series = df["owner"].astype(str).fillna("")
            df["company"] = df["company"].where(df["company"] != "", owner_series)

    for col in ["country", "resource_type", "status"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].apply(lambda x: clean_text(x, ""))

    scored_df = compute_scores(df)
    scored_df["investment_tier"] = scored_df.apply(assign_tier, axis=1)
    scored_df["recommended_action_v2"] = scored_df["investment_tier"].apply(default_action)
    scored_df["strategy_detail_v2"] = scored_df.apply(build_strategy_detail, axis=1)
    scored_df["key_risk_note"] = scored_df.apply(build_risk_note, axis=1)

    legacy_lookup = build_legacy_lookup(load_dataframe(OLD_INPUT))
    merged_actions = []
    merged_details = []
    for _, row in scored_df.iterrows():
        key = (
            clean_text(row.get("project_name", row.get("project", ""))),
            clean_text(row.get("country", "")),
            clean_text(row.get("resource_type", "")),
        )
        legacy = legacy_lookup.get(key, {})
        merged_actions.append(
            legacy.get("recommended_action") or row["recommended_action_v2"]
        )
        merged_details.append(
            legacy.get("strategy_detail") or row["strategy_detail_v2"]
        )

    scored_df["recommended_action_v2"] = merged_actions
    scored_df["strategy_detail_v2"] = merged_details

    scored_df = scored_df.sort_values(
        by=["strategic_investment_score", "price_margin_wan", "strategic_aisc_wan"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    scored_df["rank"] = range(1, len(scored_df) + 1)

    numeric_round_cols = [
        "annual_capacity",
        "effective_capacity",
        "base_aisc_wan",
        "adjusted_aisc_wan",
        "strategic_aisc_wan",
        "strategy_base_aisc_wan",
        "policy_risk_premium_wan",
        "policy_risk_premium_pct",
        "adjusted_minus_base_wan",
        "strategic_minus_adjusted_wan",
        "current_lce_price_wan",
        "price_margin_wan",
        "price_margin_pct",
        "strategic_aisc_percentile",
        "capacity_score",
        "cost_score",
        "margin_score",
        "policy_risk_score_norm",
        "strategic_investment_score",
        "score_percentile",
    ]
    for col in numeric_round_cols:
        if col in scored_df.columns:
            scored_df[col] = pd.to_numeric(scored_df[col], errors="coerce").fillna(0).round(4)

    scored_df["policy_premium_flag"] = scored_df["policy_premium_flag"].astype(bool)

    for col in OUTPUT_COLUMNS:
        if col not in scored_df.columns:
            scored_df[col] = ""

    return scored_df[OUTPUT_COLUMNS]


def write_empty_output():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=OUTPUT_COLUMNS).to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    input_df, _ = load_inputs()

    if input_df.empty:
        write_empty_output()
        print("项目数：0")
        print(f"输出路径：{OUTPUT}")
        print("Tier分布：无")
        print("Top 10项目：无")
        print("价格倒挂项目数：0")
        print("政策溢价项目数：0")
        return

    result_df = build_recommendations(input_df)
    result_df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    top_10 = result_df[["rank", "project_name", "country", "strategic_investment_score"]].head(10)
    price_inversion_count = int((result_df["price_margin_wan"] < 0).sum())
    premium_count = int(result_df["policy_premium_flag"].astype(bool).sum())
    tier_1_df = result_df[result_df["investment_tier"] == "Tier 1｜优先锁定"][
        ["rank", "project_name", "country", "strategic_investment_score", "score_percentile"]
    ].head(10)
    percentile_check = result_df[
        ["project_name", "strategic_investment_score", "score_percentile", "investment_tier"]
    ].head(10)

    print(f"项目数：{len(result_df)}")
    print(f"输出路径：{OUTPUT}")
    print("Tier分布：")
    print(result_df["investment_tier"].value_counts(dropna=False).to_string())
    print("Top 10项目：")
    print(top_10.to_string(index=False))
    print(f"价格倒挂项目数：{price_inversion_count}")
    print(f"政策溢价项目数：{premium_count}")
    print("Top 10 Tier 1项目：")
    if tier_1_df.empty:
        print("无")
    else:
        print(tier_1_df.to_string(index=False))
    print("percentile分布检查：")
    print(percentile_check.to_string(index=False))


if __name__ == "__main__":
    main()
