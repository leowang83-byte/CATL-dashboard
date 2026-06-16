import pandas as pd


def generate_recommendation_action(row, predicted_price_center):
    """
    规则模型只负责生成 recommended_action。
    AI 策略建议改为在 dashboard.py 中按需生成。
    """
    country = str(row.get("country", ""))
    delivered_cost = float(row.get("delivered_cost", 0) or 0)
    risk_score = float(row.get("risk_score", 0.5) or 0.5)

    export_ban = bool(row.get("export_ban", False))
    local_processing = bool(row.get("local_processing_required", False))

    if delivered_cost < 45000 and risk_score < 0.5:
        return "战略控股 / 大股权锁定"

    if export_ban or local_processing:
        return "本地选矿 + 初级冶炼合资"

    if "Australia" in country or "澳大利亚" in country:
        return "小股权 + 包销 + 能源改造"

    if delivered_cost > predicted_price_center:
        return "暂缓投资 / 仅保留谈判权"

    if risk_score >= 0.7:
        return "高风险观察"

    return "少数股权 + 长协锁量"


def calculate_investment_score(row):
    """
    投资评分：分数越高，优先级越高。
    """
    delivered_cost = float(row.get("delivered_cost", 0) or 0)
    risk_score = float(row.get("risk_score", 0.5) or 0.5)

    if delivered_cost <= 0:
        cost_score = 0
    else:
        cost_score = max(0, 1 - delivered_cost / 200000)

    score = 0.65 * cost_score + 0.35 * (1 - risk_score)

    return round(score, 4)


def build_investment_recommendations(df, predicted_price_center):
    output = df.copy()

    output["investment_score"] = output.apply(calculate_investment_score, axis=1)

    output["recommended_action"] = output.apply(
        lambda row: generate_recommendation_action(row, predicted_price_center),
        axis=1
    )

    # 不在 main.py 中批量生成 AI 策略，避免看板和主流程变慢
    output["strategy_detail"] = ""

    columns = [
        "name",
        "country",
        "resource_type",
        "annual_capacity",
        "effective_capacity",
        "aisc_cost",
        "energy_cost",
        "transport_cost",
        "realtime_aisc",
        "adjusted_aisc",
        "delivered_cost",
        "policy_supply_shock",
        "policy_cost_shock",
        "policy_delay_months",
        "affected_lce_tonnes",
        "policy_risk_score",
        "event_risk_score",
        "event_count",
        "negative_event_count",
        "latest_event_title",
        "risk_score",
        "investment_score",
        "recommended_action",
        "strategy_detail",
    ]

    existing_columns = [col for col in columns if col in output.columns]

    return output[existing_columns].sort_values(
        "investment_score",
        ascending=False
    )