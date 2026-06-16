from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"

CRITICAL_EVENTS_FILE = REPORTS_DIR / "weekly_critical_events.csv"
CATL_IMPACT_FILE = REPORTS_DIR / "weekly_catl_impact.csv"
DECISION_ACTIONS_FILE = REPORTS_DIR / "weekly_decision_actions.csv"
WEEKLY_AI_BRIEF_FILE = REPORTS_DIR / "weekly_ai_brief.csv"

CATL_COUNTRIES = {
    "argentina",
    "chile",
    "australia",
    "zimbabwe",
    "brazil",
    "canada",
    "china",
    "ghana",
    "mali",
    "drc",
    "bolivia",
    "阿根廷",
    "智利",
    "澳洲",
    "澳大利亚",
    "津巴布韦",
    "巴西",
    "加拿大",
    "中国",
    "加纳",
    "马里",
    "刚果金",
    "玻利维亚",
}

LITHIUM_KEYWORDS = [
    "lithium",
    "spodumene",
    "brine",
    "lce",
    "lithium carbonate",
    "lithium hydroxide",
    "carbonate",
    "锂",
    "锂辉石",
    "盐湖",
    "碳酸锂",
    "氢氧化锂",
]

TRUSTED_SOURCE_KEYWORDS = [
    "mining.com",
    "smm",
    "fastmarkets",
    "benchmark",
    "company announcement",
    "official",
    "exchange",
]

DISCLOSURE_RELEVANCE_KEYWORDS = [
    "production guidance",
    "shipment guidance",
    "delay",
    "suspension",
    "capex increase",
    "resource estimate",
    "offtake",
    "acquisition",
    "产量指引",
    "出货指引",
    "延期",
    "停产",
    "资本开支增加",
    "成本上升",
    "资源量",
    "储量",
    "包销",
    "收购",
]

DISCLOSURE_SCORING_ANNOUNCEMENT_TYPES = {
    "production_guidance",
    "project_update",
    "capex_change",
    "resource_update",
    "offtake_or_mna",
    "financial_report",
}

ANNOUNCEMENT_EVENT_TYPE_MAP = {
    "production_guidance": "供给增加",
    "project_update": "项目审批",
    "capex_change": "政策变化",
    "resource_update": "项目审批",
    "offtake_or_mna": "投资交易",
    "financial_report": "其他",
    "policy_or_legal": "政策变化",
}

EVENT_RULES = [
    ("供给收缩", ["shutdown", "suspension", "halt", "curtailment", "restart", "production cut", "停产", "暂停", "减产", "复产"]),
    ("产量指引变化", ["production guidance", "shipment guidance", "output guidance", "guidance cut", "lower guidance", "指引", "产量指引", "出货指引", "下修"]),
    ("政策收紧", ["export ban", "export restriction", "ban", "restriction", "quota", "出口限制", "出口禁令", "配额", "禁令"]),
    ("政策变化", ["royalty", "tax", "mining law", "concession", "license", "permit", "资源税", "矿业税", "特许权", "许可证", "审批"]),
    ("项目变化", ["delay", "delayed", "capex increase", "cost overrun", "budget overrun", "延期", "推迟", "成本超支", "资本开支上升"]),
    ("供给增加", ["expansion", "ramp up", "commissioning", "投产", "扩产"]),
    ("投资交易", ["offtake", "acquisition", "merger", "m&a", "joint venture", "divestment", "收购", "包销", "并购", "合资", "出售"]),
    ("项目审批", ["permit", "approval", "license", "审批", "许可"]),
    ("库存变化", ["inventory", "stockpile", "库存"]),
    ("价格异常", ["price spike", "price drop", "涨价", "跌价"]),
]

SEVERITY_SCORE = {
    "供给收缩": 40,
    "产量指引变化": 40,
    "政策收紧": 45,
    "出口限制": 45,
    "政策变化": 35,
    "项目变化": 35,
    "供给增加": 25,
    "项目审批": 25,
    "投资交易": 30,
    "库存变化": 20,
    "价格异常": 20,
}

OUTLOOK_KEYWORDS = [
    "market outlook",
    "industry outlook",
    "forecast",
    "demand growth",
    "battery demand",
    "ev demand",
    "price forecast",
    "analyst says",
    "market report",
    "行业展望",
    "市场预测",
    "需求增长",
    "机构预测",
    "分析师认为",
    "价格预测",
    "市场报告",
]

PRODUCTION_PROJECT_KEYWORDS = [
    "production",
    "capacity",
    "commissioning",
    "ramp up",
    "shutdown",
    "suspension",
    "halt",
    "curtailment",
    "restart",
    "产量",
    "产能",
    "投产",
    "停产",
    "暂停",
    "减产",
    "复产",
]

POLICY_KEYWORDS = [
    "policy",
    "royalty",
    "tax",
    "mining law",
    "concession",
    "license",
    "permit",
    "export ban",
    "export restriction",
    "restriction",
    "quota",
    "政策",
    "资源税",
    "矿业税",
    "特许权",
    "许可证",
    "审批",
    "出口限制",
    "出口禁令",
    "配额",
]


def load_csv(file_name: str) -> pd.DataFrame:
    path = REPORTS_DIR / file_name
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def safe_str(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def parse_date(value) -> pd.Timestamp | None:
    if value is None or safe_str(value) == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed


def make_event_id(*parts: str) -> str:
    raw = "|".join(safe_str(part) for part in parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def text_blob(*parts: str) -> str:
    return " ".join(safe_str(part) for part in parts).lower()


def is_mostly_english(text: str) -> bool:
    text = safe_str(text)
    if not text:
        return False
    ascii_letters = len(re.findall(r"[A-Za-z]", text))
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return ascii_letters > max(cjk_chars * 2, 8)


def translate_text(text: str) -> str:
    text = safe_str(text)
    if not text:
        return ""
    if not is_mostly_english(text):
        return text

    replacements = [
        ("lithium", "锂"),
        ("Lithium", "锂"),
        ("spodumene", "锂辉石"),
        ("Spodumene", "锂辉石"),
        ("brine", "盐湖卤水"),
        ("Brine", "盐湖卤水"),
        ("lithium carbonate", "碳酸锂"),
        ("Lithium carbonate", "碳酸锂"),
        ("lithium hydroxide", "氢氧化锂"),
        ("Lithium hydroxide", "氢氧化锂"),
        ("mine", "矿山"),
        ("Mine", "矿山"),
        ("project", "项目"),
        ("Project", "项目"),
        ("shutdown", "停产"),
        ("Shutdown", "停产"),
        ("suspension", "暂停"),
        ("Suspension", "暂停"),
        ("restart", "复产"),
        ("Restart", "复产"),
        ("export ban", "出口禁令"),
        ("Export ban", "出口禁令"),
        ("export restriction", "出口限制"),
        ("Export restriction", "出口限制"),
        ("royalty", "特许权使用费"),
        ("Royalty", "特许权使用费"),
        ("tax", "税费"),
        ("Tax", "税费"),
        ("production", "产量"),
        ("Production", "产量"),
        ("guidance", "指引"),
        ("Guidance", "指引"),
        ("offtake", "包销"),
        ("Offtake", "包销"),
        ("acquisition", "收购"),
        ("Acquisition", "收购"),
        ("approval", "审批"),
        ("Approval", "审批"),
        ("permit", "许可"),
        ("Permit", "许可"),
        ("delay", "延期"),
        ("Delay", "延期"),
    ]
    translated = text
    for source, target in replacements:
        translated = translated.replace(source, target)
    return translated


def strip_news_source_suffix(title: str) -> str:
    title = safe_str(title)
    if not title:
        return ""
    # Many RSS titles append the publisher after the final dash; remove it before generating Chinese titles.
    parts = re.split(r"\s[-–—]\s", title)
    if len(parts) > 1 and len(parts[-1]) <= 40:
        return " - ".join(parts[:-1]).strip()
    return title


def build_title_subject(country: str, company: str, project: str) -> str:
    parts = []
    if safe_str(company):
        parts.append(safe_str(company))
    if safe_str(project):
        project_text = safe_str(project)
        if "project" not in project_text.lower() and "项目" not in project_text:
            project_text = f"{project_text}项目"
        parts.append(project_text)
    if parts:
        return " ".join(parts)
    if safe_str(country):
        return f"{safe_str(country)}锂资源"
    return "锂资源事件"


def translate_title_by_context(title: str, event_type: str, country: str, company: str, project: str) -> str:
    original = safe_str(title)
    if not original or not is_mostly_english(original):
        return original

    clean_title = strip_news_source_suffix(original)
    blob = clean_title.lower()
    subject = build_title_subject(country, company, project)
    has_glencore = "glencore" in blob

    if any(word in blob for word in ["restart", "restarts", "restarting", "restarted", "recommission"]):
        if has_glencore:
            return f"{subject}重启推进，Glencore参与复产支持"
        return f"{subject}重启复产"

    if any(word in blob for word in ["shutdown", "suspension", "halt", "curtailment", "production cut"]):
        return f"{subject}出现停产、暂停或减产信号"

    if any(word in blob for word in ["production guidance", "shipment guidance", "output guidance", "guidance cut", "lower guidance"]):
        return f"{subject}产量或出货指引发生变化"

    if any(word in blob for word in ["export ban", "export restriction", "quota", "ban", "restriction"]):
        return f"{subject}面临出口限制或政策收紧"

    if any(word in blob for word in ["royalty", "tax", "mining law", "concession", "license", "permit"]):
        return f"{subject}涉及税费、矿业法或许可政策变化"

    if any(word in blob for word in ["delay", "delayed", "capex increase", "cost overrun", "budget overrun"]):
        return f"{subject}出现项目延期或资本开支上升"

    if any(word in blob for word in ["offtake", "acquisition", "merger", "m&a", "joint venture", "divestment"]):
        return f"{subject}出现包销、并购或合资交易进展"

    if any(word in blob for word in ["approval", "approved", "commissioning", "ramp up", "ramp-up"]):
        return f"{subject}项目审批、投产或爬坡进展更新"

    if any(word in blob for word in ["price spike", "price drop", "share price", "stock"]):
        return f"{subject}价格或资本市场表现出现波动"

    if "lithium" in blob or "spodumene" in blob or "brine" in blob:
        event_text = safe_str(event_type) or "资源事件"
        return f"{subject}：{event_text}"

    return ""


def contextual_title_cn(title: str, event_type: str, country: str, company: str, project: str) -> str:
    contextual = translate_title_by_context(title, event_type, country, company, project)
    if contextual:
        return contextual
    translated = translate_text(title)
    if translated and not is_mostly_english(translated):
        return translated
    parts = []
    if safe_str(country):
        parts.append(safe_str(country))
    if safe_str(company):
        parts.append(safe_str(company))
    if safe_str(project):
        parts.append(safe_str(project))
    subject = " / ".join(parts) if parts else "锂资源"
    event_text = safe_str(event_type) or "重大事件"
    return f"{subject}：{event_text}"


def contextual_summary_cn(summary: str, event_type: str, country: str, company: str, project: str) -> str:
    translated = translate_text(summary)
    if translated and not is_mostly_english(translated):
        return translated
    title_like = contextual_title_cn("", event_type, country, company, project)
    return f"{title_like}，需关注对供应安全、采购成本和资源配置节奏的影响。"


def classify_event(title: str, summary: str = "", fallback: str = "") -> str:
    blob = text_blob(title, summary, fallback)
    for event_type, keywords in EVENT_RULES:
        if any(keyword.lower() in blob for keyword in keywords):
            return event_type
    fallback_text = safe_str(fallback)
    if fallback_text and fallback_text != "general_lithium_resource_news":
        return fallback_text
    return "其他"


def infer_impact_direction(event_type: str, existing_direction: str = "") -> str:
    direction = safe_str(existing_direction).lower()
    if direction in {"negative", "负面"}:
        return "负面"
    if direction in {"positive", "正面"}:
        return "正面"
    if event_type in {"供给收缩", "政策收紧", "政策变化", "价格异常"}:
        return "负面"
    if event_type in {"供给增加", "投资交易", "项目审批"}:
        return "正面"
    return "中性"


def infer_price_direction(event_type: str, impact_direction: str, price_shock: float = 0.0) -> str:
    if price_shock > 0:
        return "上行"
    if price_shock < 0:
        return "下行"
    if event_type in {"供给收缩", "政策收紧"}:
        return "上行"
    if event_type == "供给增加":
        return "下行"
    if impact_direction == "负面":
        return "上行"
    return "中性"


def source_score(source: str, event_source_category: str = "") -> int:
    source_lower = safe_str(source).lower()
    if event_source_category == "disclosure":
        return 25
    if any(keyword in source_lower for keyword in TRUSTED_SOURCE_KEYWORDS):
        return 20
    if "google news" in source_lower or "rss" in source_lower:
        return 12
    return 5


def recency_score(published_at) -> int:
    published = parse_date(published_at)
    if published is None:
        return 0
    now = pd.Timestamp(datetime.now())
    if published.tzinfo is not None:
        published = published.tz_convert(None)
    days = max((now - published).days, 0)
    if days <= 7:
        return 20
    if days <= 30:
        return 10
    return 0


def priority_bucket(score: float) -> str:
    if score >= 85:
        return "P1"
    if score >= 70:
        return "P2"
    if score >= 65:
        return "P3"
    return "Watch"


def event_nature(event_type: str) -> str:
    if event_type in {"供给收缩", "产量指引变化"}:
        return "供应扰动"
    if event_type in {"政策收紧", "政策变化"}:
        return "政策变化"
    if event_type in {"项目变化", "项目审批", "供给增加"}:
        return "项目变化"
    if event_type == "投资交易":
        return "交易事件"
    if event_type in {"库存变化", "价格异常"}:
        return "市场观察"
    return "重大冲击"


def confidence_level(score: float, source: str, published_at, event_source_category: str = "") -> str:
    total = source_score(source, event_source_category) + recency_score(published_at)
    if score >= 80 and total >= 30:
        return "高"
    if score >= 50:
        return "中"
    return "低"


def build_project_lookup(*frames: pd.DataFrame) -> list[dict]:
    projects: list[dict] = []
    seen = set()
    for frame in frames:
        if frame.empty:
            continue
        for _, row in frame.iterrows():
            name = safe_str(row.get("name", row.get("project_name", "")))
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            projects.append(
                {
                    "name": name,
                    "country": safe_str(row.get("country", "")),
                    "resource_type": safe_str(row.get("resource_type", "")),
                    "owner": safe_str(row.get("owner", "")),
                }
            )
    return projects


def match_project_company(title: str, summary: str, projects: list[dict]) -> tuple[str, str, str]:
    blob = text_blob(title, summary)
    for project in projects:
        name = project["name"]
        owner = project["owner"]
        if name and name.lower() in blob:
            return name, owner, project["resource_type"]
        if owner and owner.lower() in blob:
            return name, owner, project["resource_type"]
    return "", "", ""


def infer_resource_type(title: str, summary: str, existing: str = "") -> str:
    if safe_str(existing):
        return safe_str(existing)
    blob = text_blob(title, summary)
    if "spodumene" in blob or "锂辉石" in blob:
        return "spodumene"
    if "brine" in blob or "盐湖" in blob:
        return "brine"
    if "mica" in blob or "云母" in blob:
        return "mica"
    if "recycling" in blob or "回收" in blob:
        return "recycling"
    if any(keyword.lower() in blob for keyword in LITHIUM_KEYWORDS):
        return "lithium"
    return ""


def catl_relevance_score(country: str, title: str, summary: str, project: str, company: str) -> int:
    score = 0
    country_text = safe_str(country).lower()
    blob = text_blob(title, summary)
    if country_text in CATL_COUNTRIES:
        score += 20
    if any(keyword.lower() in blob for keyword in LITHIUM_KEYWORDS):
        score += 20
    if safe_str(project) or safe_str(company):
        score += 30
    return score


def specificity_score(country: str, title: str, summary: str, project: str, company: str) -> int:
    score = 0
    country_value = safe_str(country)
    project_value = safe_str(project)
    company_value = safe_str(company)
    blob = text_blob(title, summary, country_value, project_value, company_value)

    if company_value and project_value:
        score += 20
    if company_value and country_value:
        score += 15
    if project_value and any(keyword.lower() in blob for keyword in PRODUCTION_PROJECT_KEYWORDS):
        score += 25
    if country_value and any(keyword.lower() in blob for keyword in POLICY_KEYWORDS):
        score += 25
    return score


def should_cap_outlook_event(title: str, summary: str, country: str, project: str, company: str) -> bool:
    blob = text_blob(title, summary)
    has_outlook_keyword = any(keyword.lower() in blob for keyword in OUTLOOK_KEYWORDS)
    if not has_outlook_keyword:
        return False

    has_specific_anchor = bool(safe_str(country) or safe_str(project) or safe_str(company))
    has_policy_or_production = any(
        keyword.lower() in blob
        for keyword in POLICY_KEYWORDS + PRODUCTION_PROJECT_KEYWORDS
    )
    return not has_specific_anchor and not has_policy_or_production


def event_summary(row: pd.Series, event_type: str, title: str) -> str:
    title_cn = safe_str(row.get("title_cn", ""))
    if title_cn and title_cn != title:
        return title_cn
    if event_type == "库存变化":
        return "库存指标出现变化，需要结合现货成交、仓单和排产节奏判断价格影响。"
    if event_type == "价格异常":
        return "价格指标出现异常波动，需要复盘采购节奏和套保区间。"
    return safe_str(row.get("summary", "")) or title


def make_event(
    *,
    published_at,
    source: str,
    source_url: str,
    title: str,
    summary: str,
    country: str,
    company: str,
    project: str,
    resource_type: str,
    event_type: str,
    impact_direction: str,
    supply_impact_lce: float,
    price_impact_direction: str,
    projects: list[dict],
    event_source_category: str = "news",
    relevance_floor: int = 0,
) -> dict:
    if not project and not company:
        matched_project, matched_company, matched_resource = match_project_company(title, summary, projects)
        project = matched_project
        company = matched_company
        if not resource_type:
            resource_type = matched_resource

    resource_type = infer_resource_type(title, summary, resource_type)
    relevance = catl_relevance_score(country, title, summary, project, company)
    if relevance_floor > 0:
        relevance = max(relevance, relevance_floor)
    severity = SEVERITY_SCORE.get(event_type, 10)
    specificity = specificity_score(country, title, summary, project, company)
    score = (
        severity
        + relevance
        + specificity
        + source_score(source, event_source_category)
        + recency_score(published_at)
    )
    if should_cap_outlook_event(title, summary, country, project, company):
        score = min(score, 45)
    level = priority_bucket(score)
    title_cn = contextual_title_cn(title, event_type, country, company, project)
    summary_cn = contextual_summary_cn(summary, event_type, country, company, project)

    return {
        "event_id": make_event_id(published_at, source, title, country),
        "event_source_category": event_source_category,
        "published_at": safe_str(published_at),
        "source": source or "未知来源",
        "source_url": source_url,
        "title": title,
        "title_cn": title_cn,
        "summary": summary,
        "summary_cn": summary_cn,
        "country": country,
        "company": company,
        "project": project,
        "resource_type": resource_type,
        "event_type": event_type,
        "event_nature": event_nature(event_type),
        "impact_direction": impact_direction,
        "event_priority_score": round(score, 2),
        "priority_level": level,
        "catl_relevance_score": relevance,
        "supply_impact_lce": supply_impact_lce,
        "price_impact_direction": price_impact_direction,
        "confidence_level": confidence_level(score, source, published_at, event_source_category),
        "is_top_event": False,
    }


def events_from_news(news_df: pd.DataFrame, projects: list[dict]) -> list[dict]:
    events = []
    if news_df.empty:
        return events

    for _, row in news_df.iterrows():
        title = safe_str(row.get("title_cn", "")) or safe_str(row.get("title", ""))
        if not title:
            continue
        summary = event_summary(row, safe_str(row.get("event_type", "")), title)
        event_type = classify_event(title, summary, safe_str(row.get("event_type", "")))
        impact_direction = infer_impact_direction(event_type, safe_str(row.get("impact_direction", "")))
        price_shock = safe_float(row.get("price_shock", 0))
        events.append(
            make_event(
                published_at=row.get("published_at", row.get("created_at", "")),
                source=safe_str(row.get("source", "")),
                source_url=safe_str(row.get("url", "")),
                title=title,
                summary=summary,
                country=safe_str(row.get("country", "")),
                company="",
                project="",
                resource_type=infer_resource_type(title, summary),
                event_type=event_type,
                impact_direction=impact_direction,
                supply_impact_lce=safe_float(row.get("supply_shock", 0)),
                price_impact_direction=infer_price_direction(event_type, impact_direction, price_shock),
                projects=projects,
                event_source_category="news",
            )
        )
    return events


def events_from_raw_news(raw_news_df: pd.DataFrame, projects: list[dict]) -> list[dict]:
    events = []
    if raw_news_df.empty:
        return events

    for _, row in raw_news_df.iterrows():
        title = safe_str(row.get("title", ""))
        if not title:
            continue
        summary = safe_str(row.get("summary", ""))
        raw_text = safe_str(row.get("raw_text", ""))
        event_type = classify_event(title, f"{summary} {raw_text}", "")
        impact_direction = infer_impact_direction(event_type, "")
        events.append(
            make_event(
                published_at=row.get("published_at", row.get("ingested_at", "")),
                source=safe_str(row.get("source", "")),
                source_url=safe_str(row.get("source_url", "")),
                title=title,
                summary=summary or raw_text[:500] or title,
                country=safe_str(row.get("country", "")),
                company=safe_str(row.get("company", "")),
                project=safe_str(row.get("project", "")),
                resource_type=safe_str(row.get("resource_type", "")) or infer_resource_type(title, summary),
                event_type=event_type,
                impact_direction=impact_direction,
                supply_impact_lce=0,
                price_impact_direction=infer_price_direction(event_type, impact_direction, 0),
                projects=projects,
                event_source_category="news",
            )
        )
    return events


def disclosure_relevance_floor(row: pd.Series, title: str, summary: str, raw_text: str) -> int:
    announcement_type = safe_str(row.get("announcement_type", ""))
    blob = text_blob(title, summary, raw_text, safe_str(row.get("keyword_hit", "")))
    if announcement_type in DISCLOSURE_SCORING_ANNOUNCEMENT_TYPES:
        return 20
    if any(keyword.lower() in blob for keyword in DISCLOSURE_RELEVANCE_KEYWORDS):
        return 20
    return 0


def disclosure_event_type(row: pd.Series, title: str, summary: str, raw_text: str) -> str:
    announcement_type = safe_str(row.get("announcement_type", ""))
    event_type = classify_event(title, f"{summary} {raw_text}", "")
    if event_type != "其他":
        return event_type
    return ANNOUNCEMENT_EVENT_TYPE_MAP.get(announcement_type, "其他")


def events_from_disclosure(disclosure_df: pd.DataFrame, projects: list[dict]) -> list[dict]:
    events = []
    if disclosure_df.empty:
        return events

    for _, row in disclosure_df.iterrows():
        title = safe_str(row.get("title", ""))
        if not title:
            continue
        if is_generic_disclosure_landing(
            title,
            safe_str(row.get("source", "")),
            safe_str(row.get("source_url", "")),
        ):
            continue
        summary = safe_str(row.get("summary", ""))
        raw_text = safe_str(row.get("raw_text", ""))
        announcement_type = safe_str(row.get("announcement_type", ""))
        if announcement_type not in DISCLOSURE_SCORING_ANNOUNCEMENT_TYPES and not keyword_is_relevant(title, summary, raw_text):
            continue

        event_type = disclosure_event_type(row, title, summary, raw_text)
        impact_direction = infer_impact_direction(event_type, "")
        relevance_floor = disclosure_relevance_floor(row, title, summary, raw_text)
        events.append(
            make_event(
                published_at=row.get("published_at", row.get("ingested_at", "")),
                source=safe_str(row.get("source", "")),
                source_url=safe_str(row.get("source_url", "")),
                title=title,
                summary=summary or raw_text[:500] or title,
                country=safe_str(row.get("country", "")),
                company=safe_str(row.get("company", "")),
                project=safe_str(row.get("project", "")),
                resource_type=safe_str(row.get("resource_type", "")) or infer_resource_type(title, summary),
                event_type=event_type,
                impact_direction=impact_direction,
                supply_impact_lce=0,
                price_impact_direction=infer_price_direction(event_type, impact_direction, 0),
                projects=projects,
                event_source_category="disclosure",
                relevance_floor=relevance_floor,
            )
        )
    return events


def keyword_is_relevant(*parts: str) -> bool:
    blob = text_blob(*parts)
    return any(keyword.lower() in blob for keyword in LITHIUM_KEYWORDS + DISCLOSURE_RELEVANCE_KEYWORDS)


def is_generic_disclosure_landing(title: str, source: str, source_url: str = "") -> bool:
    title_lower = safe_str(title).lower()
    source_lower = safe_str(source).lower()
    url_lower = safe_str(source_url).lower()
    generic_title_keywords = [
        "investor centre",
        "investor center",
        "latest news",
        "announcements",
        "asx releases",
        "news releases",
        "press releases",
        "quarterly report results",
        "for personal use only",
        "中矿资源集团股份有限公司",
        "青海盐湖工业股份有限公司",
        "天齐锂业股份有限公司",
    ]
    if any(keyword in title_lower for keyword in generic_title_keywords):
        return True
    if "investor relations" in source_lower and any(
        token in url_lower for token in ["investor", "announcement", "news"]
    ):
        title_words = [word for word in re.split(r"\W+", title_lower) if word]
        return len(title_words) <= 6
    return False


def events_from_country_risk(country_df: pd.DataFrame, projects: list[dict]) -> list[dict]:
    events = []
    if country_df.empty:
        return events

    for _, row in country_df.iterrows():
        title = safe_str(row.get("latest_event_title_cn", "")) or safe_str(row.get("latest_event_title", ""))
        if not title:
            continue
        event_type = classify_event(title, "", safe_str(row.get("latest_event_type", "")))
        impact_direction = "负面" if safe_float(row.get("event_risk_score", 0)) >= 0.65 else "中性"
        events.append(
            make_event(
                published_at=datetime.now().strftime("%Y-%m-%d"),
                source="country_event_risk",
                source_url="",
                title=title,
                summary=f"{safe_str(row.get('country', ''))} 最新事件风险评分为 {safe_float(row.get('event_risk_score', 0)):.2f}。",
                country=safe_str(row.get("country", "")),
                company="",
                project="",
                resource_type=infer_resource_type(title, ""),
                event_type=event_type,
                impact_direction=impact_direction,
                supply_impact_lce=safe_float(row.get("total_supply_shock", 0)),
                price_impact_direction=infer_price_direction(event_type, impact_direction, safe_float(row.get("total_price_shock", 0))),
                projects=projects,
                event_source_category="policy",
            )
        )
    return events


def events_from_policy(policy_df: pd.DataFrame, projects: list[dict]) -> list[dict]:
    if policy_df.empty:
        return []

    row = policy_df.iloc[0]
    supply_loss_ratio = safe_float(row.get("supply_loss_ratio", 0))
    aisc_uplift = safe_float(row.get("aisc_uplift", 0))
    expected_price = safe_float(row.get("expected_lce_price", 0))
    if supply_loss_ratio <= 0 and aisc_uplift <= 0 and expected_price <= 0:
        return []

    title = "政策与供给扰动推升锂资源成本压力"
    summary = (
        f"模型显示供给损失比例约 {supply_loss_ratio:.2%}，"
        f"AISC抬升约 {aisc_uplift:.0f} 元/吨，需复核项目成本和政策假设。"
    )
    return [
        make_event(
            published_at=datetime.now().strftime("%Y-%m-%d"),
            source="policy_price_impact.csv",
            source_url="",
            title=title,
            summary=summary,
            country="Global",
            company="",
            project="",
            resource_type="lithium",
            event_type="政策变化",
            impact_direction="负面",
            supply_impact_lce=0,
            price_impact_direction="上行",
            projects=projects,
            event_source_category="policy",
        )
    ]


def events_from_market_inputs(weekly_df: pd.DataFrame, projects: list[dict]) -> list[dict]:
    if weekly_df.empty:
        return []

    row = weekly_df.iloc[0]
    events = []
    inventory_days = safe_float(row.get("inventory_days", 0))
    gfex_price = safe_float(row.get("gfex_futures_price", 0))
    spot_price = safe_float(row.get("mmlc_spot_price", row.get("battery_lce_mid", 0)))
    source = safe_str(row.get("price_source", "weekly_price_inputs.csv")) or "weekly_price_inputs.csv"
    published_at = safe_str(row.get("updated_at", datetime.now().strftime("%Y-%m-%d")))

    if inventory_days > 0:
        title = "碳酸锂库存天数触发周度监测"
        if inventory_days <= 14:
            summary = f"当前库存约 {inventory_days:.1f} 天，已进入价格反弹窗口观察区。"
            impact_direction = "负面"
            price_direction = "上行"
        elif inventory_days <= 21:
            summary = f"当前库存约 {inventory_days:.1f} 天，库存压力有所缓解但仍需观察成交和仓单变化。"
            impact_direction = "中性"
            price_direction = "中性"
        else:
            summary = f"当前库存约 {inventory_days:.1f} 天，库存仍高于关键阈值，价格上行弹性受压。"
            impact_direction = "负面"
            price_direction = "下行"

        events.append(
            make_event(
                published_at=published_at,
                source=source,
                source_url="",
                title=title,
                summary=summary,
                country="China",
                company="",
                project="",
                resource_type="LCE",
                event_type="库存变化",
                impact_direction=impact_direction,
                supply_impact_lce=0,
                price_impact_direction=price_direction,
                projects=projects,
                event_source_category="market",
            )
        )

    if gfex_price > 0 and spot_price > 0:
        spread = (gfex_price - spot_price) / spot_price
        if abs(spread) >= 0.03:
            direction = "上行" if spread > 0 else "下行"
            events.append(
                make_event(
                    published_at=published_at,
                    source=source,
                    source_url="",
                    title="GFEX碳酸锂价格与现货价格出现偏离",
                    summary=f"GFEX价格相对现货偏离约 {spread:.1%}，需要复盘采购节奏与套保区间。",
                    country="China",
                    company="",
                    project="",
                    resource_type="LCE",
                    event_type="价格异常",
                    impact_direction="负面",
                    supply_impact_lce=0,
                    price_impact_direction=direction,
                    projects=projects,
                    event_source_category="market",
                )
            )
    return events


def dedupe_events(events: list[dict]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame(columns=[
            "event_id",
            "event_source_category",
            "published_at",
            "source",
            "source_url",
            "title",
            "title_cn",
            "summary",
            "summary_cn",
            "country",
            "company",
            "project",
            "resource_type",
            "event_type",
            "event_nature",
            "impact_direction",
            "event_priority_score",
            "priority_level",
            "catl_relevance_score",
            "supply_impact_lce",
            "price_impact_direction",
            "confidence_level",
            "is_top_event",
        ])

    df = pd.DataFrame(events)
    df = df.sort_values("event_priority_score", ascending=False)
    df = df.drop_duplicates(subset=["title", "country"], keep="first")
    eligible_top = df[df["event_priority_score"].apply(lambda value: safe_float(value) >= 65)].copy()
    if not eligible_top.empty:
        top_ids = set(eligible_top.head(5)["event_id"].tolist())
    else:
        top_ids = set(df.head(min(len(df), 3))["event_id"].tolist())
    df["is_top_event"] = df["event_id"].isin(top_ids)
    return df


def build_catl_impact(events_df: pd.DataFrame, country_risk_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    risk_map = {}
    if not country_risk_df.empty and "country" in country_risk_df.columns:
        risk_map = {
            safe_str(row.get("country", "")): safe_float(row.get("event_risk_score", 0))
            for _, row in country_risk_df.iterrows()
        }

    for _, event in events_df.iterrows():
        event_type = safe_str(event.get("event_type", ""))
        score = safe_float(event.get("event_priority_score", 0))
        bucket = priority_bucket(score)
        country = safe_str(event.get("country", ""))
        country_risk = risk_map.get(country, 0)

        supply_security = "高" if event_type in {"供给收缩", "政策收紧", "产量指引变化"} else "中" if event_type in {"政策变化", "项目审批", "项目变化"} else "低"
        procurement_cost = "高" if event_type in {"价格异常", "供给收缩", "产量指引变化", "项目变化"} else "中" if event_type in {"库存变化", "政策收紧", "政策变化"} else "低"
        opportunity = "高" if event_type in {"投资交易", "项目审批"} and safe_str(event.get("impact_direction")) == "正面" else "中" if event_type in {"投资交易", "项目审批", "政策变化", "项目变化"} else "低"
        geopolitical = "高" if event_type == "政策收紧" or country_risk >= 0.65 else "中" if country_risk >= 0.35 or event_type in {"政策变化", "项目变化"} else "低"
        impact_level = "高" if bucket == "P1" else "中" if bucket == "P2" else "低"

        exposure_parts = []
        if country:
            exposure_parts.append(country)
        if safe_str(event.get("project", "")):
            exposure_parts.append(safe_str(event.get("project", "")))
        if safe_str(event.get("resource_type", "")):
            exposure_parts.append(safe_str(event.get("resource_type", "")))
        catl_exposure = " / ".join(exposure_parts) if exposure_parts else "通用资源敞口"

        rows.append(
            {
                "event_id": event["event_id"],
                "supply_security_impact": supply_security,
                "procurement_cost_impact": procurement_cost,
                "investment_opportunity_impact": opportunity,
                "geopolitical_risk_impact": geopolitical,
                "catl_exposure": catl_exposure,
                "impact_level": impact_level,
                "impact_summary": make_impact_summary(event, supply_security, procurement_cost, opportunity, geopolitical),
            }
        )

    return pd.DataFrame(rows)


def make_impact_summary(event: pd.Series, supply: str, cost: str, opportunity: str, geo: str) -> str:
    event_type = safe_str(event.get("event_type", ""))
    country = safe_str(event.get("country", "相关区域")) or "相关区域"
    title = safe_str(event.get("title", "本周事件"))

    if event_type in {"供给收缩", "政策收紧"}:
        return f"{country}事件可能影响资源可得性，建议立即评估替代资源、采购安全库存和项目推进节奏。"
    if event_type == "政策变化":
        return f"{country}政策变量正在改变项目经济性，建议复核税费、合规成本和投资回报假设。"
    if event_type == "投资交易":
        return f"{title}可能改变优质资源竞争格局，建议判断是否需要进入优先接触或跟踪清单。"
    if event_type == "项目审批":
        return f"{country}项目审批进展会影响未来供给兑现，建议更新项目投产概率和资源池排序。"
    if event_type == "库存变化":
        return f"库存信号影响短期采购窗口，建议结合现货成交、仓单和排产变化调整采购节奏。"
    if event_type == "价格异常":
        return f"价格异常波动会影响采购成本和套保边界，建议本周完成价格与采购节奏复盘。"
    return f"该事件对供给安全为{supply}、采购成本为{cost}、投资机会为{opportunity}、地缘风险为{geo}，建议纳入周度跟踪。"


def build_decision_actions(events_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, event in events_df.iterrows():
        event_type = safe_str(event.get("event_type", ""))
        score = safe_float(event.get("event_priority_score", 0))
        bucket = priority_bucket(score)

        if bucket == "P1" and event_type in {"供给收缩", "政策收紧", "产量指引变化"}:
            decision_type = "立即决策"
        elif bucket in {"P1", "P2"}:
            decision_type = "授权跟进"
        else:
            decision_type = "继续观察"

        recommended_action, owner_team = action_for_event(event_type)
        urgency = "高" if decision_type == "立即决策" else "中" if decision_type == "授权跟进" else "低"
        deadline = "本周内" if decision_type == "立即决策" else "两周内" if decision_type == "授权跟进" else "持续跟踪"

        rows.append(
            {
                "event_id": event["event_id"],
                "decision_type": decision_type,
                "recommended_action": recommended_action,
                "urgency": urgency,
                "owner_team": owner_team,
                "deadline": deadline,
                "trigger_condition": f"{bucket} / {event_type} / 分数 {score:.0f}",
                "status": "待处理",
            }
        )
    return pd.DataFrame(rows)


def split_lines(items: list[str], limit: int = 3) -> str:
    clean_items = []
    for item in items:
        item = safe_str(item)
        if item and item not in clean_items:
            clean_items.append(item)
    return "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(clean_items[:limit]))


def build_weekly_ai_brief(critical_events_df: pd.DataFrame, decision_actions_df: pd.DataFrame) -> pd.DataFrame:
    now = datetime.now()
    columns = [
        "brief_date",
        "overall_judgement",
        "price_outlook",
        "supply_outlook",
        "investment_outlook",
        "risk_outlook",
        "recommended_actions",
        "watch_items",
        "confidence_level",
        "generated_from_event_ids",
        "updated_at",
    ]

    if critical_events_df.empty or "is_top_event" not in critical_events_df.columns:
        return pd.DataFrame([
            {
                "brief_date": now.strftime("%Y-%m-%d"),
                "overall_judgement": "本周未出现重大资源冲击事件，维持既有资源配置判断。",
                "price_outlook": "中性",
                "supply_outlook": "平稳",
                "investment_outlook": "维持跟踪",
                "risk_outlook": "平稳",
                "recommended_actions": "1. 维持重点资源国和Priority项目跟踪。",
                "watch_items": "1. 跟踪重点资源国政策与项目公告更新。",
                "confidence_level": "低",
                "generated_from_event_ids": "",
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ], columns=columns)

    top_df = critical_events_df[
        critical_events_df["is_top_event"].astype(str).str.lower().isin(["true", "1", "yes"])
    ].copy()
    if top_df.empty:
        return pd.DataFrame([
            {
                "brief_date": now.strftime("%Y-%m-%d"),
                "overall_judgement": "本周未出现重大资源冲击事件，维持既有资源配置判断。",
                "price_outlook": "中性",
                "supply_outlook": "平稳",
                "investment_outlook": "维持跟踪",
                "risk_outlook": "平稳",
                "recommended_actions": "1. 维持重点资源国和Priority项目跟踪。",
                "watch_items": "1. 跟踪重点资源国政策与项目公告更新。",
                "confidence_level": "低",
                "generated_from_event_ids": "",
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ], columns=columns)

    event_types = top_df["event_type"].astype(str).tolist() if "event_type" in top_df.columns else []
    titles = top_df.get("title_cn", top_df.get("title", pd.Series(dtype=str))).astype(str).tolist()
    countries = top_df.get("country", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
    companies = top_df.get("company", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
    event_ids = top_df.get("event_id", pd.Series(dtype=str)).dropna().astype(str).tolist()

    supply_tight_types = {"供给收缩", "产量指引变化"}
    policy_risk_types = {"政策收紧", "政策变化"}
    investment_positive_types = {"投资交易", "项目审批", "供给增加"}
    price_positive_types = {"价格异常", "库存变化"}

    supply_outlook = "偏紧" if any(event_type in supply_tight_types for event_type in event_types) else "平稳"
    risk_outlook = "上升" if any(event_type in policy_risk_types for event_type in event_types) else "平稳"
    investment_outlook = "改善" if any(event_type in investment_positive_types for event_type in event_types) else "保持筛选"

    price_outlook = "中性"
    if any(event_type in price_positive_types for event_type in event_types):
        joined = text_blob(*titles)
        if any(word in joined for word in ["price drop", "库存上升", "下行", "跌价"]):
            price_outlook = "偏弱"
        else:
            price_outlook = "偏强"

    focus_region = "、".join([item for item in countries if item and item.lower() != "nan"][:3]) or "重点资源国"
    focus_company = "、".join([item for item in companies if item and item.lower() != "nan"][:3]) or "重点资源公司"
    focus_event = "；".join([item for item in titles if item and item.lower() != "nan"][:3])

    overall_judgement = (
        f"本周资源战略情报显示，{focus_region}相关事件仍是影响资源安全与采购节奏的核心变量。"
        f"TOP事件集中在{focus_event}等方向，说明短期资源端并非单纯价格波动，而是受到政策、项目进度、供给扰动和交易竞争共同影响。"
        f"从资源事业部视角看，供应判断应以可兑现产能和政策执行风险为主线，不能只看名义产能；采购判断应同步评估库存窗口、期货价格与现货成交；投资判断应继续向低成本、低风险、可锁量项目集中。"
        f"当前供应展望为{supply_outlook}，风险展望为{risk_outlook}，投资窗口判断为{investment_outlook}。"
        f"建议本周围绕{focus_company}及相关资源国重新检查锁量假设、项目推进优先级和采购安全库存安排，避免在政策或项目扰动放大后被动调整。"
    )
    if len(overall_judgement) < 200:
        overall_judgement += (
            "后续应把公告、交易所披露和资源国政策文本作为第一优先级信息源，"
            "并将重大事件同步映射到供应安全、采购成本、投资机会和地缘风险四个管理维度。"
        )

    actions = []
    if supply_outlook == "偏紧":
        actions.append("授权资源投资团队复核澳洲锂辉石和重点盐湖项目锁量假设。")
        actions.append("要求采购团队评估未来两周补库窗口和安全库存安排。")
    if risk_outlook == "上升":
        actions.append("暂缓高政策风险国家新增项目推进，并更新资源风险敞口。")
        actions.append("要求法务合规团队复核相关国家税费、出口和审批条款。")
    if investment_outlook == "改善":
        actions.append("将包销、并购和审批进展明确的项目纳入优先接触清单。")
    if not actions:
        actions.append("维持重点资源国和Priority项目跟踪。")

    if not decision_actions_df.empty and "recommended_action" in decision_actions_df.columns:
        action_candidates = (
            decision_actions_df["recommended_action"]
            .dropna()
            .astype(str)
            .tolist()
        )
        actions.extend(action_candidates)

    watch_items = []
    if risk_outlook == "上升":
        watch_items.append("资源国政策正式文本、执行时间和适用项目范围。")
    if supply_outlook == "偏紧":
        watch_items.append("重点矿山是否出现进一步减产、停产或产量指引下修。")
    if investment_outlook == "改善":
        watch_items.append("交易价格、包销条款、审批进度和交割条件。")
    if price_outlook != "中性":
        watch_items.append("GFEX、SMM库存、仓单变化和现货成交。")
    if not watch_items:
        watch_items.append("重点资源国政策与项目公告更新。")

    confidence = "高" if len(top_df) >= 5 else "中" if len(top_df) >= 3 else "低"

    return pd.DataFrame([
        {
            "brief_date": now.strftime("%Y-%m-%d"),
            "overall_judgement": overall_judgement,
            "price_outlook": price_outlook,
            "supply_outlook": supply_outlook,
            "investment_outlook": investment_outlook,
            "risk_outlook": risk_outlook,
            "recommended_actions": split_lines(actions, 3),
            "watch_items": split_lines(watch_items, 3),
            "confidence_level": confidence,
            "generated_from_event_ids": ";".join(event_ids),
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
    ], columns=columns)


def action_for_event(event_type: str) -> tuple[str, str]:
    if event_type == "供给收缩":
        return "评估替代资源与采购安全库存", "采购"
    if event_type == "产量指引变化":
        return "复核供应缺口、采购节奏和安全库存安排", "采购"
    if event_type == "政策收紧":
        return "更新该国资源风险敞口，暂停新增高风险项目推进", "战略"
    if event_type == "政策变化":
        return "要求法务和资源投资团队复核项目假设", "法务合规"
    if event_type == "项目变化":
        return "更新项目进度、投产概率和资本开支假设", "资源投资"
    if event_type == "投资交易":
        return "评估是否纳入优先接触清单", "资源投资"
    if event_type == "项目审批":
        return "更新项目开发进度和投产概率", "资源投资"
    if event_type == "价格异常":
        return "启动价格与采购节奏复盘", "市场研究"
    if event_type == "库存变化":
        return "复核库存、仓单和采购节奏", "供应链"
    if event_type == "供给增加":
        return "评估新增供给对长期包销窗口的影响", "战略"
    return "纳入周度资源情报跟踪", "市场研究"


def run_engine() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_news_df = load_csv("raw_news_events.csv")
    raw_disclosure_df = load_csv("raw_disclosure_events.csv")
    has_raw_event_pool = not raw_news_df.empty or not raw_disclosure_df.empty
    news_df = load_csv("news_event_summary.csv") if not has_raw_event_pool else pd.DataFrame()
    country_risk_df = load_csv("country_event_risk.csv")
    policy_df = load_csv("policy_price_impact.csv") if not has_raw_event_pool else pd.DataFrame()
    weekly_df = load_csv("weekly_price_inputs.csv")
    invest_df = load_csv("investment_recommendations.csv")
    cost_df = load_csv("dynamic_cost_curve.csv")

    projects = build_project_lookup(invest_df, cost_df)

    events = []
    if has_raw_event_pool:
        events.extend(events_from_raw_news(raw_news_df, projects))
        events.extend(events_from_disclosure(raw_disclosure_df, projects))
    else:
        events.extend(events_from_news(news_df, projects))
        events.extend(events_from_country_risk(country_risk_df, projects))
        events.extend(events_from_policy(policy_df, projects))
    events.extend(events_from_market_inputs(weekly_df, projects))

    critical_events_df = dedupe_events(events)
    critical_events_df.to_csv(CRITICAL_EVENTS_FILE, index=False, encoding="utf-8-sig")

    actionable_events_df = critical_events_df[
        critical_events_df["event_priority_score"].apply(lambda value: safe_float(value) >= 65)
    ].copy()

    catl_impact_df = build_catl_impact(actionable_events_df, country_risk_df)
    decision_actions_df = build_decision_actions(actionable_events_df)
    weekly_ai_brief_df = build_weekly_ai_brief(critical_events_df, decision_actions_df)

    catl_impact_df.to_csv(CATL_IMPACT_FILE, index=False, encoding="utf-8-sig")
    decision_actions_df.to_csv(DECISION_ACTIONS_FILE, index=False, encoding="utf-8-sig")
    weekly_ai_brief_df.to_csv(WEEKLY_AI_BRIEF_FILE, index=False, encoding="utf-8-sig")

    return critical_events_df, catl_impact_df, decision_actions_df


def main() -> None:
    run_engine()
    print("已生成：")
    print("reports/weekly_critical_events.csv")
    print("reports/weekly_catl_impact.csv")
    print("reports/weekly_decision_actions.csv")
    print("reports/weekly_ai_brief.csv")


if __name__ == "__main__":
    main()
