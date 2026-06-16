import os
from dotenv import load_dotenv


def fallback_strategy(row, predicted_price_center, rule_action):
    """
    当没有 OpenAI API Key、SDK未安装、或API调用失败时，使用本地兜底建议。
    """
    country = str(row.get("country", ""))
    resource_type = str(row.get("resource_type", ""))
    delivered_cost = float(row.get("delivered_cost", 0) or 0)
    risk_score = float(row.get("risk_score", 0.5) or 0.5)
    event_title = str(row.get("latest_event_title", "") or "")

    if delivered_cost < predicted_price_center * 0.6 and risk_score < 0.5:
        return (
            f"{country}{resource_type}项目成本显著低于价格中枢，建议优先开展股权进入或长期包销谈判，"
            f"重点锁定低成本资源安全边际。"
        )

    if risk_score >= 0.7:
        return (
            f"{country}项目当前综合风险偏高，建议暂缓重资产投入，仅保留信息跟踪和期权式合作。"
            f"近期事件参考：{event_title[:80]}"
        )

    if delivered_cost > predicted_price_center:
        return (
            f"该项目交付成本高于预测价格中枢，短期不建议控股投资，可作为长协谈判或周期底部备选标的。"
        )

    return (
        f"该项目具备一定资源价值，建议采用少数股权、长协锁量或技术合作方式进入，"
        f"同时持续跟踪政策、物流和新闻事件变化。"
    )


def build_ai_prompt(row, predicted_price_center, rule_action):
    """
    构建给 AI 的投资建议 Prompt。
    """
    project_name = row.get("name", "")
    country = row.get("country", "")
    resource_type = row.get("resource_type", "")
    annual_capacity = row.get("annual_capacity", "")
    aisc_cost = row.get("aisc_cost", "")
    realtime_aisc = row.get("realtime_aisc", "")
    delivered_cost = row.get("delivered_cost", "")
    policy_risk_score = row.get("policy_risk_score", "")
    event_risk_score = row.get("event_risk_score", "")
    risk_score = row.get("risk_score", "")
    export_ban = row.get("export_ban", "")
    local_processing_required = row.get("local_processing_required", "")
    latest_event_title = row.get("latest_event_title", "")

    prompt = f"""
你是宁德时代时代资源国际矿产投资研究员。请基于以下结构化数据，为 CATL 生成一条专属投资建议。

要求：
1. 用中文输出。
2. 不要写成模板句，要结合项目数据给出判断。
3. 重点围绕：是否适合控股、是否适合包销、是否需要本地选矿/初级冶炼、是否应暂缓。
4. 输出 120-180 字。
5. 不要编造不存在的数据。
6. 结论要清晰，适合放入 investment_recommendations.csv 的 strategy_detail 栏。

项目数据：
- 项目名称：{project_name}
- 国家：{country}
- 资源类型：{resource_type}
- 年产能：{annual_capacity}
- 基准 AISC：{aisc_cost}
- 动态 AISC：{realtime_aisc}
- 交付成本：{delivered_cost}
- 预测碳酸锂价格中枢：{predicted_price_center}
- 政策风险分：{policy_risk_score}
- 新闻事件风险分：{event_risk_score}
- 综合风险分：{risk_score}
- 是否存在出口禁令：{export_ban}
- 是否要求本地加工：{local_processing_required}
- 近期新闻事件：{latest_event_title}
- 系统初步分类：{rule_action}

请直接输出投资建议正文，不要加标题。
"""
    return prompt.strip()


def generate_ai_strategy(row, predicted_price_center, rule_action):
    """
    调用 OpenAI API 生成 strategy_detail。
    如果失败，自动使用 fallback_strategy。
    """
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        return fallback_strategy(row, predicted_price_center, rule_action)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        prompt = build_ai_prompt(
            row=row,
            predicted_price_center=predicted_price_center,
            rule_action=rule_action
        )

        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=300,
        )

        text = response.output_text.strip()

        if not text:
            return fallback_strategy(row, predicted_price_center, rule_action)

        return text

    except Exception as exc:
        return fallback_strategy(row, predicted_price_center, rule_action)