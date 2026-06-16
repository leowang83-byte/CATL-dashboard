from pathlib import Path

import os
import pandas as pd
from dotenv import load_dotenv


REPORTS_DIR = Path("reports")


# =========================
# 论文基准参数
# =========================
# 单位说明：
# LCE 价格：元/吨
# GFEX：元/吨
# SC6：美元/吨
# AISC：元/吨
# 库存：天
# 开工率：0-1

PAPER_BASE_LCE_PRICE = 182000       # 论文价格中枢：18.2 万元/吨
PAPER_PRICE_LOWER = 170000          # 论文预测区间下沿：17 万元/吨
PAPER_PRICE_UPPER = 195000          # 论文预测区间上沿：19.5 万元/吨

BASE_GFEX_PRICE = 178000            # GFEX 基准价格：元/吨
BASE_SC6_PRICE = 2745               # SC6 基准价格：美元/吨
BASE_INVENTORY_DAYS = 24.7          # 库存基准天数
BASE_CATHODE_UTILIZATION = 0.72      # 正极开工率基准
BASE_AISC_90 = 175000               # 论文口径边际 AISC 防御线：元/吨


def load_csv(file_name):
    file_path = REPORTS_DIR / file_name

    if not file_path.exists():
        return pd.DataFrame()

    return pd.read_csv(file_path)


def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def load_sc6_unit_parameters():
    """
    从 .env 读取 SC6 单位转换参数。
    """
    load_dotenv()

    usd_cny = safe_float(os.getenv("USD_CNY"), 7.2)
    sc6_to_lce_conversion = safe_float(os.getenv("SC6_TO_LCE_CONVERSION"), 8.0)
    sc6_pass_through = safe_float(os.getenv("SC6_PASS_THROUGH"), 0.30)

    return usd_cny, sc6_to_lce_conversion, sc6_pass_through


def classify_price_zone(price):
    """
    根据论文逻辑，把 LCE 价格分成生产者关心的区间。
    单位：元/吨
    """
    if price < 170000:
        return (
            "出清压力区",
            "价格低于 17 万元/吨，高成本产能承压明显。生产者应控制库存、压缩高成本产线、推迟扩产，并重点观察行业出清。"
        )

    if 170000 <= price < 175000:
        return (
            "成本底部防御区",
            "价格处于 17-17.5 万元/吨，接近论文中的成本铁底区域。生产者应重点跟踪库存去化、精矿成本与高成本产能退出。"
        )

    if 175000 <= price < 182000:
        return (
            "中枢下沿运行区",
            "价格位于 17.5-18.2 万元/吨，仍有成本支撑，但利润弹性有限。生产者应维持稳健生产，优化原料结构和销售节奏。"
        )

    if 182000 <= price <= 195000:
        return (
            "核心中枢运行区",
            "价格处于论文预测核心区间 18.2-19.5 万元/吨。生产者可维持正常开工，优化长协与现货比例，并择机锁定部分利润。"
        )

    return (
        "利润扩张区",
        "价格高于 19.5 万元/吨，进入利润扩张区。生产者应加快现金回收、锁定销售价格，同时警惕高成本产能复产带来的价格回落。"
    )


def calculate_system_aisc_90(cost_df):
    """
    计算当前系统中的 90% AISC。
    如果系统样本还不完整，最终会用 max(system_aisc_90, BASE_AISC_90) 校准。
    """
    if cost_df.empty:
        return 0

    if "adjusted_aisc" in cost_df.columns:
        col = "adjusted_aisc"
    elif "realtime_aisc" in cost_df.columns:
        col = "realtime_aisc"
    elif "aisc_cost" in cost_df.columns:
        col = "aisc_cost"
    else:
        return 0

    df = cost_df.copy()
    df[col] = pd.to_numeric(df[col], errors="coerce")

    valid = df[df[col].notna() & (df[col] > 0)].copy()

    if valid.empty:
        return 0

    if "annual_capacity" in valid.columns:
        valid["annual_capacity"] = pd.to_numeric(
            valid["annual_capacity"],
            errors="coerce"
        ).fillna(0)

        valid = valid.sort_values(col)

        total_capacity = valid["annual_capacity"].sum()

        if total_capacity > 0:
            valid["cum_capacity"] = valid["annual_capacity"].cumsum()
            threshold = total_capacity * 0.9
            return float(valid[valid["cum_capacity"] >= threshold][col].iloc[0])

    return float(valid[col].quantile(0.9))


def load_weekly_inputs():
    """
    从 reports/weekly_price_inputs.csv 读取每周更新的模型输入。
    如果文件不存在，则使用论文基准值。
    """
    inputs_df = load_csv("weekly_price_inputs.csv")

    if inputs_df.empty:
        return {
            "updated_at": "",
            "gfex_futures_price": BASE_GFEX_PRICE,
            "crude_oil_price": 83.5,
            "sc6_price_index": BASE_SC6_PRICE,
            "cathode_utilization": BASE_CATHODE_UTILIZATION,
            "inventory_days": BASE_INVENTORY_DAYS,
            "data_quality_note": "Default paper-calibrated fallback inputs used.",
        }

    row = inputs_df.iloc[0]

    return {
        "updated_at": row.get("updated_at", ""),
        "gfex_futures_price": safe_float(
            row.get("gfex_futures_price"),
            BASE_GFEX_PRICE
        ),
        "crude_oil_price": safe_float(
            row.get("crude_oil_price"),
            83.5
        ),
        "sc6_price_index": safe_float(
            row.get("sc6_price_index"),
            BASE_SC6_PRICE
        ),
        "cathode_utilization": safe_float(
            row.get("cathode_utilization"),
            BASE_CATHODE_UTILIZATION
        ),
        "inventory_days": safe_float(
            row.get("inventory_days"),
            BASE_INVENTORY_DAYS
        ),
        "data_quality_note": row.get("data_quality_note", ""),
    }


def load_policy_impact():
    """
    读取政策冲击结果。
    只读取 supply_loss_ratio 和 aisc_uplift。
    不直接使用旧 policy_price_impact.csv 里的 expected_lce_price。
    """
    policy_df = load_csv("policy_price_impact.csv")

    if policy_df.empty:
        return {
            "supply_loss_ratio": 0,
            "aisc_uplift": 0,
        }

    row = policy_df.iloc[0]

    return {
        "supply_loss_ratio": safe_float(row.get("supply_loss_ratio"), 0),
        "aisc_uplift": safe_float(row.get("aisc_uplift"), 0),
    }


def calculate_sc6_lce_cost(sc6_price, usd_cny, sc6_to_lce_conversion):
    """
    把 SC6 美元/吨转换为元/吨 LCE 的矿端成本压力。

    公式：
    SC6折算LCE成本 = SC6美元价格 × USD/CNY × SC6-to-LCE单耗
    """
    return sc6_price * usd_cny * sc6_to_lce_conversion


def build_lce_price_forecast():
    """
    论文锚定 + SC6单位统一版 LCE 价格预测模型。

    核心逻辑：
    LCE预测价格 =
    论文基准价格 182000
    + GFEX 偏离修正
    + SC6 折算 LCE 成本偏离修正
    + 库存偏离修正
    + 开工率偏离修正
    + AISC90 偏离修正
    + 政策冲击溢价
    """

    REPORTS_DIR.mkdir(exist_ok=True)

    inputs = load_weekly_inputs()

    gfex_futures_price = inputs["gfex_futures_price"]
    sc6_price_index = inputs["sc6_price_index"]
    cathode_utilization = inputs["cathode_utilization"]
    inventory_days = inputs["inventory_days"]

    usd_cny, sc6_to_lce_conversion, sc6_pass_through = load_sc6_unit_parameters()

    # =========================
    # AISC90 校准
    # =========================
    cost_df = load_csv("dynamic_cost_curve.csv")
    system_aisc_90 = calculate_system_aisc_90(cost_df)

    calibrated_aisc_90 = max(system_aisc_90, BASE_AISC_90)

    # =========================
    # 政策冲击
    # =========================
    policy_impact = load_policy_impact()

    supply_loss_ratio = policy_impact["supply_loss_ratio"]
    aisc_uplift = policy_impact["aisc_uplift"]

    # =========================
    # SC6 单位统一
    # =========================
    base_sc6_lce_cost = calculate_sc6_lce_cost(
        BASE_SC6_PRICE,
        usd_cny,
        sc6_to_lce_conversion
    )

    current_sc6_lce_cost = sc6_price_index * usd_cny * sc6_to_lce_conversion
    base_sc6_lce_cost = 0
    sc6_lce_cost_change = 0
    sc6_adjustment = current_sc6_lce_cost * sc6_pass_through
    sc6_lce_cost_change = current_sc6_lce_cost - base_sc6_lce_cost

    # =========================
    # 论文锚定动态修正项
    # =========================
    gfex_adjustment = 0.30 * (gfex_futures_price - BASE_GFEX_PRICE)

    # 关键修改：
    # 旧版：sc6_adjustment = 18.0 * (SC6 - BASE_SC6)
    # 新版：先统一单位为 元/吨LCE，再乘以传导系数
    sc6_adjustment = sc6_pass_through * sc6_lce_cost_change

    inventory_adjustment = -900.0 * (inventory_days - BASE_INVENTORY_DAYS)

    utilization_adjustment = 35000.0 * (
        cathode_utilization - BASE_CATHODE_UTILIZATION
    )

    aisc_adjustment = 0.35 * (
        calibrated_aisc_90 - BASE_AISC_90
    )

    base_forecast_price = (
        PAPER_BASE_LCE_PRICE
        + gfex_adjustment
        + sc6_adjustment
        + inventory_adjustment
        + utilization_adjustment
        + aisc_adjustment
    )

    # =========================
    # 政策冲击溢价
    # =========================
    policy_supply_premium = base_forecast_price * supply_loss_ratio * 0.25

    policy_aisc_premium = aisc_uplift * 0.35

    expected_lce_price = (
        base_forecast_price
        + policy_supply_premium
        + policy_aisc_premium
    )

    # =========================
    # 模型稳定器
    # =========================
    model_floor = PAPER_PRICE_LOWER * 0.92
    model_ceiling = PAPER_PRICE_UPPER * 1.15

    expected_lce_price = min(
        max(expected_lce_price, model_floor),
        model_ceiling
    )

    lower_bound = max(expected_lce_price * 0.93, PAPER_PRICE_LOWER * 0.95)
    upper_bound = min(expected_lce_price * 1.07, PAPER_PRICE_UPPER * 1.10)

    price_zone, producer_strategy = classify_price_zone(expected_lce_price)

    output = {
        "updated_at": inputs["updated_at"],
        "model_version": "paper_calibrated_sc6_unit_v3",

        "paper_base_lce_price": PAPER_BASE_LCE_PRICE,
        "paper_price_lower": PAPER_PRICE_LOWER,
        "paper_price_upper": PAPER_PRICE_UPPER,

        "gfex_futures_price": round(gfex_futures_price, 2),
        "crude_oil_price": round(inputs["crude_oil_price"], 2),
        "sc6_price_index_usd_per_tonne": round(sc6_price_index, 2),
        "usd_cny": round(usd_cny, 4),
        "sc6_to_lce_conversion": round(sc6_to_lce_conversion, 4),
        "sc6_pass_through": round(sc6_pass_through, 4),

        "base_sc6_lce_cost": round(base_sc6_lce_cost, 2),
        "current_sc6_lce_cost": round(current_sc6_lce_cost, 2),
        "sc6_lce_cost_change": round(sc6_lce_cost_change, 2),
        "sc6_adjustment": round(sc6_adjustment, 2),

        "cathode_utilization": round(cathode_utilization, 4),
        "inventory_days": round(inventory_days, 2),

        "system_aisc_90": round(system_aisc_90, 2),
        "calibrated_aisc_90": round(calibrated_aisc_90, 2),

        "supply_loss_ratio": round(supply_loss_ratio, 4),
        "aisc_uplift": round(aisc_uplift, 2),

        "gfex_adjustment": round(gfex_adjustment, 2),
        "inventory_adjustment": round(inventory_adjustment, 2),
        "utilization_adjustment": round(utilization_adjustment, 2),
        "aisc_adjustment": round(aisc_adjustment, 2),
        "policy_supply_premium": round(policy_supply_premium, 2),
        "policy_aisc_premium": round(policy_aisc_premium, 2),

        "base_forecast_price": round(base_forecast_price, 2),
        "expected_lce_price": round(expected_lce_price, 2),
        "lower_bound": round(lower_bound, 2),
        "upper_bound": round(upper_bound, 2),

        "price_zone": price_zone,
        "producer_strategy": producer_strategy,

        "data_quality_note": (
            str(inputs["data_quality_note"])
            + " | SC6 is converted from USD/t concentrate into RMB/t LCE-equivalent cost "
            + "using USD_CNY × SC6_TO_LCE_CONVERSION, then passed through to LCE price "
            + "with SC6_PASS_THROUGH."
        ),
    }

    output_df = pd.DataFrame([output])

    output_df.to_csv(
        REPORTS_DIR / "lce_price_forecast.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("LCE price forecast saved to reports/lce_price_forecast.csv")
    print(output_df.to_string(index=False))

    return output_df


if __name__ == "__main__":
    build_lce_price_forecast()
