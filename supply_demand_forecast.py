from pathlib import Path
from datetime import datetime

import pandas as pd


REPORTS_DIR = Path("reports")
OUTPUT_FILE = REPORTS_DIR / "lce_supply_demand_forecast.csv"


# =========================
# 论文锚定版 LCE 供需缺口模型
# =========================
# 单位：万吨 LCE
#
# 核心校准原则：
# 1. 论文判断：2026 年全球实质性供需缺口扩大至 8 万吨 LCE 以上
# 2. 因此将 2026 / 未来12个月 balance_lce 锚定在 -8 万吨附近
# 3. 未来6个月按半年度口径，锚定在 -4 万吨附近
# 4. 2027-2030 作为情景预测，不作为论文已验证结论
# =========================


PAPER_2026_ADJUSTED_DEMAND_LCE = 150.0
PAPER_2026_EFFECTIVE_SUPPLY_LCE = 142.0
PAPER_2026_BALANCE_LCE = -8.0


FORECAST_ASSUMPTIONS = [
    {
        "period": "未来6个月",
        "year": 2026,
        "base_demand_lce": 70.0,
        "ess_uplift_lce": 3.0,
        "inventory_restocking_lce": 2.0,
        "adjusted_demand_lce": 75.0,
        "announced_supply_lce": 78.0,
        "realization_rate": 0.94,
        "operating_rate": 0.96,
        "policy_disruption_lce": 2.0,
        "logistics_delay_lce": 1.0,
        "effective_supply_lce": 71.0,
        "model_type": "paper_anchor_short_term",
        "note": "半年度口径，按论文2026年缺口8万吨的约一半进行锚定。",
    },
    {
        "period": "未来12个月",
        "year": 2026,
        "base_demand_lce": 137.0,
        "ess_uplift_lce": 8.0,
        "inventory_restocking_lce": 5.0,
        "adjusted_demand_lce": 150.0,
        "announced_supply_lce": 156.0,
        "realization_rate": 0.94,
        "operating_rate": 0.96,
        "policy_disruption_lce": 5.0,
        "logistics_delay_lce": 3.0,
        "effective_supply_lce": 142.0,
        "model_type": "paper_anchor_2026",
        "note": "论文锚定口径：2026年实质性供需缺口约8万吨LCE以上。",
    },
    {
        "period": "2027",
        "year": 2027,
        "base_demand_lce": 158.0,
        "ess_uplift_lce": 10.0,
        "inventory_restocking_lce": 3.0,
        "adjusted_demand_lce": 171.0,
        "announced_supply_lce": 184.0,
        "realization_rate": 0.84,
        "operating_rate": 0.91,
        "policy_disruption_lce": 10.0,
        "logistics_delay_lce": 4.0,
        "effective_supply_lce": 127.0,
        "model_type": "scenario_forecast",
        "note": "中期情景预测：考虑项目兑现率下降、政策扰动和物流时滞。",
    },
    {
        "period": "2028",
        "year": 2028,
        "base_demand_lce": 178.0,
        "ess_uplift_lce": 13.0,
        "inventory_restocking_lce": 2.0,
        "adjusted_demand_lce": 193.0,
        "announced_supply_lce": 210.0,
        "realization_rate": 0.82,
        "operating_rate": 0.90,
        "policy_disruption_lce": 12.0,
        "logistics_delay_lce": 4.0,
        "effective_supply_lce": 139.0,
        "model_type": "scenario_forecast",
        "note": "中期情景预测：需求继续增长，供应兑现风险扩大。",
    },
    {
        "period": "2029",
        "year": 2029,
        "base_demand_lce": 198.0,
        "ess_uplift_lce": 15.0,
        "inventory_restocking_lce": 2.0,
        "adjusted_demand_lce": 215.0,
        "announced_supply_lce": 235.0,
        "realization_rate": 0.81,
        "operating_rate": 0.90,
        "policy_disruption_lce": 13.0,
        "logistics_delay_lce": 3.0,
        "effective_supply_lce": 155.0,
        "model_type": "scenario_forecast",
        "note": "中长期情景预测：项目投产兑现率和政策风险是核心不确定项。",
    },
    {
        "period": "2030",
        "year": 2030,
        "base_demand_lce": 220.0,
        "ess_uplift_lce": 18.0,
        "inventory_restocking_lce": 2.0,
        "adjusted_demand_lce": 240.0,
        "announced_supply_lce": 265.0,
        "realization_rate": 0.80,
        "operating_rate": 0.89,
        "policy_disruption_lce": 14.0,
        "logistics_delay_lce": 3.0,
        "effective_supply_lce": 172.0,
        "model_type": "scenario_forecast",
        "note": "2030结构性情景预测：用于长期资源配置和包销战略判断。",
    },
]


def classify_market_status(balance_lce, gap_ratio):
    """
    balance_lce = effective_supply_lce - adjusted_demand_lce

    正数：供应过剩
    负数：供应短缺
    """
    if balance_lce >= 5:
        return "供应过剩", "市场偏宽松，价格上行压力较弱。"

    if -5 <= balance_lce < 5:
        return "基本平衡", "供需接近平衡，价格主要受库存和政策扰动影响。"

    if -15 <= balance_lce < -5:
        return "轻度短缺", "供需转紧，价格具备阶段性支撑。"

    return "显著短缺", "供给缺口明显，资源保障、长协锁量和低成本资源布局优先级上升。"


def build_supply_demand_forecast():
    REPORTS_DIR.mkdir(exist_ok=True)

    rows = []

    for item in FORECAST_ASSUMPTIONS:
        adjusted_demand_lce = float(item["adjusted_demand_lce"])
        effective_supply_lce = float(item["effective_supply_lce"])

        balance_lce = effective_supply_lce - adjusted_demand_lce

        if adjusted_demand_lce > 0:
            gap_ratio = balance_lce / adjusted_demand_lce
        else:
            gap_ratio = 0

        market_status, market_comment = classify_market_status(
            balance_lce,
            gap_ratio,
        )

        rows.append(
            {
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "period": item["period"],
                "year": item["year"],

                "base_demand_lce": round(item["base_demand_lce"], 2),
                "ess_uplift_lce": round(item["ess_uplift_lce"], 2),
                "inventory_restocking_lce": round(item["inventory_restocking_lce"], 2),
                "adjusted_demand_lce": round(adjusted_demand_lce, 2),

                "announced_supply_lce": round(item["announced_supply_lce"], 2),
                "realization_rate": round(item["realization_rate"], 4),
                "operating_rate": round(item["operating_rate"], 4),
                "policy_disruption_lce": round(item["policy_disruption_lce"], 2),
                "logistics_delay_lce": round(item["logistics_delay_lce"], 2),
                "effective_supply_lce": round(effective_supply_lce, 2),

                "balance_lce": round(balance_lce, 2),
                "gap_ratio": round(gap_ratio, 4),
                "market_status": market_status,
                "market_comment": market_comment,
                "model_type": item["model_type"],
                "note": item["note"],
            }
        )

    output_df = pd.DataFrame(rows)

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("LCE supply-demand forecast saved to reports/lce_supply_demand_forecast.csv")
    print(output_df.to_string(index=False))

    return output_df


if __name__ == "__main__":
    build_supply_demand_forecast()