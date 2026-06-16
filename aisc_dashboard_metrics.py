from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")
INPUT = REPORTS_DIR / "project_strategic_aisc_v2.csv"
OUTPUT = REPORTS_DIR / "aisc_dashboard_metrics.csv"
CURRENT_LCE_PRICE_WAN = 18.20


def load_project_aisc():
    if not INPUT.exists():
        print("warning: project_strategic_aisc_v2.csv not found")
        return pd.DataFrame()

    try:
        df = pd.read_csv(INPUT, encoding="utf-8-sig")
    except Exception:
        try:
            df = pd.read_csv(INPUT)
        except Exception:
            print("warning: failed to read project_strategic_aisc_v2.csv")
            return pd.DataFrame()

    return df


def find_capacity_column(df):
    candidates = [
        "effective_capacity",
        "annual_capacity",
        "capacity_lce",
        "annual_capacity_lce",
        "capacity",
    ]
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _to_numeric_series(df, column_name):
    if column_name not in df.columns:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    return pd.to_numeric(df[column_name], errors="coerce").fillna(0.0)


def _first_existing_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _format_metric(value, decimals=2):
    if pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    try:
        return round(float(value), decimals)
    except Exception:
        return value


def build_metrics(df):
    columns = ["metric_name", "metric_value", "metric_unit", "metric_desc"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    if "strategic_aisc_wan" not in df.columns:
        print("warning: strategic_aisc_wan column missing, generating empty metrics")
        return pd.DataFrame(columns=columns)

    work = df.copy()
    for col in [
        "strategic_aisc_wan",
        "adjusted_aisc_wan",
        "base_aisc_wan",
        "policy_risk_premium_wan",
        "strategic_risk_premium_wan",
        "adjusted_minus_base_wan",
        "strategic_minus_adjusted_wan",
    ]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0.0)

    project_name_col = _first_existing_column(work, ["project_name", "project", "name"])
    capacity_col = find_capacity_column(work)
    policy_premium_col = _first_existing_column(
        work,
        ["policy_risk_premium_wan", "strategic_risk_premium_wan"],
    )

    strategic = pd.to_numeric(work["strategic_aisc_wan"], errors="coerce").fillna(0.0)
    adjusted = pd.to_numeric(work.get("adjusted_aisc_wan", 0), errors="coerce").fillna(0.0)
    base = pd.to_numeric(work.get("base_aisc_wan", 0), errors="coerce").fillna(0.0)

    if capacity_col:
        capacity = pd.to_numeric(work[capacity_col], errors="coerce").fillna(0.0)
        valid = capacity > 0
        if valid.any() and capacity[valid].sum() > 0:
            weighted_avg_strategic = (strategic[valid] * capacity[valid]).sum() / capacity[valid].sum()
            weighted_avg_desc = f"按 {capacity_col} 加权计算。"
        else:
            weighted_avg_strategic = strategic.mean() if len(strategic) else 0.0
            weighted_avg_desc = f"存在 {capacity_col} 字段，但无有效产能值，使用简单平均。"
    else:
        weighted_avg_strategic = strategic.mean() if len(strategic) else 0.0
        weighted_avg_desc = "无有效产能字段，使用简单平均。"

    strategic_p90 = strategic.quantile(0.90) if len(strategic) else 0.0
    strategic_mean = strategic.mean() if len(strategic) else 0.0
    high_policy_premium_mask = (
        pd.to_numeric(work[policy_premium_col], errors="coerce").fillna(0.0) > 0
        if policy_premium_col
        else pd.Series([False] * len(work), index=work.index)
    )
    below_price_mask = strategic <= CURRENT_LCE_PRICE_WAN
    above_price_mask = strategic > CURRENT_LCE_PRICE_WAN

    operational_adjustment_avg = (
        pd.to_numeric(work["adjusted_minus_base_wan"], errors="coerce").fillna(0.0).mean()
        if "adjusted_minus_base_wan" in work.columns
        else (adjusted - base).mean()
    )
    strategic_premium_avg = (
        pd.to_numeric(work["strategic_minus_adjusted_wan"], errors="coerce").fillna(0.0).mean()
        if "strategic_minus_adjusted_wan" in work.columns
        else (strategic - adjusted).mean()
    )

    top_policy_idx = None
    if policy_premium_col:
        top_policy_idx = pd.to_numeric(work[policy_premium_col], errors="coerce").fillna(0.0).idxmax()
    top_strategic_idx = strategic.idxmax() if len(strategic) else None
    low_strategic_idx = strategic.idxmin() if len(strategic) else None

    def get_project_name(idx):
        if idx is None or idx not in work.index or project_name_col is None:
            return ""
        return str(work.loc[idx, project_name_col])

    metrics = []

    def add_metric(name, value, unit, desc):
        metrics.append(
            {
                "metric_name": name,
                "metric_value": value,
                "metric_unit": unit,
                "metric_desc": desc,
            }
        )

    add_metric("project_count", int(len(work)), "个", "项目总数。")
    add_metric(
        "weighted_avg_strategic_aisc_wan",
        _format_metric(weighted_avg_strategic, 2),
        "万元/吨",
        f"产能加权平均战略AISC。{weighted_avg_desc}",
    )
    add_metric("strategic_aisc_p90_wan", _format_metric(strategic_p90, 2), "万元/吨", "项目库90%战略AISC线。")
    add_metric("strategic_aisc_mean_wan", _format_metric(strategic_mean, 2), "万元/吨", "项目库简单平均战略AISC。")
    add_metric("current_lce_price_wan", _format_metric(CURRENT_LCE_PRICE_WAN, 2), "万元/吨", "当前LCE价格。")
    add_metric(
        "price_margin_vs_weighted_avg_wan",
        _format_metric(CURRENT_LCE_PRICE_WAN - weighted_avg_strategic, 2),
        "万元/吨",
        "当前LCE价格减去产能加权平均战略AISC。",
    )
    add_metric(
        "price_margin_vs_p90_wan",
        _format_metric(CURRENT_LCE_PRICE_WAN - strategic_p90, 2),
        "万元/吨",
        "当前LCE价格减去项目库90%战略AISC。",
    )
    add_metric(
        "high_policy_premium_project_count",
        int(high_policy_premium_mask.sum()),
        "个",
        "政策/战略风险溢价大于0的项目数。",
    )
    add_metric(
        "high_policy_premium_project_ratio",
        _format_metric(high_policy_premium_mask.mean() if len(work) else 0.0, 4),
        "ratio",
        "高政策溢价项目占比。",
    )
    add_metric(
        "projects_below_current_price_count",
        int(below_price_mask.sum()),
        "个",
        "战略AISC低于或等于当前LCE价格的项目数。",
    )
    add_metric(
        "projects_above_current_price_count",
        int(above_price_mask.sum()),
        "个",
        "战略AISC高于当前LCE价格的项目数。",
    )
    add_metric(
        "strategic_aisc_below_price_ratio",
        _format_metric(below_price_mask.mean() if len(work) else 0.0, 4),
        "ratio",
        "战略AISC低于或等于当前LCE价格的项目占比。",
    )
    add_metric(
        "operational_adjustment_avg_wan",
        _format_metric(operational_adjustment_avg, 2),
        "万元/吨",
        "平均运营调整。",
    )
    add_metric(
        "strategic_premium_avg_wan",
        _format_metric(strategic_premium_avg, 2),
        "万元/吨",
        "平均政策/战略风险溢价。",
    )
    add_metric(
        "top_policy_premium_project",
        get_project_name(top_policy_idx),
        "项目",
        "政策/战略风险溢价最高项目名称。",
    )
    add_metric(
        "top_strategic_aisc_project",
        get_project_name(top_strategic_idx),
        "项目",
        "战略AISC最高项目名称。",
    )
    add_metric(
        "lowest_strategic_aisc_project",
        get_project_name(low_strategic_idx),
        "项目",
        "战略AISC最低项目名称。",
    )

    return pd.DataFrame(metrics, columns=columns)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_project_aisc()
    metrics_df = build_metrics(df)
    metrics_df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("saved:", OUTPUT)
    print("metric rows:", len(metrics_df))
    if not metrics_df.empty:
        core_names = {
            "weighted_avg_strategic_aisc_wan",
            "strategic_aisc_p90_wan",
            "price_margin_vs_p90_wan",
            "high_policy_premium_project_count",
        }
        core_metrics = metrics_df[metrics_df["metric_name"].isin(core_names)]
        print(core_metrics[["metric_name", "metric_value", "metric_unit"]].to_string(index=False))


if __name__ == "__main__":
    main()
