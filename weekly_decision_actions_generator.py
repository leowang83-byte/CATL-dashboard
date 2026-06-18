"""
Generate reports/weekly_decision_actions.csv from weekly_critical_events.csv.

Purpose
-------
This script turns weekly critical lithium-resource events into CATL-facing
recommended actions. The dashboard should read weekly_decision_actions.csv;
data generation stays in the weekly update pipeline.

Inputs
------
- reports/weekly_critical_events.csv
- reports/weekly_catl_impact.csv  (optional, matched by event_id)

Output
------
- reports/weekly_decision_actions.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

CRITICAL_EVENTS_FILE = "weekly_critical_events.csv"
CATL_IMPACT_FILE = "weekly_catl_impact.csv"
OUTPUT_FILE = "weekly_decision_actions.csv"

OUTPUT_COLUMNS = [
    "event_id",
    "decision_type",
    "recommended_action",
    "urgency",
    "owner_team",
    "deadline",
    "trigger_condition",
    "status",
    "created_at",
    "source_published_at",
    "event_type",
    "priority_level",
    "event_priority_score",
]


def resolve_input_file(file_name: str) -> Path:
    """Prefer reports/<file>, fallback to the script directory for ad-hoc runs."""
    reports_path = REPORTS_DIR / file_name
    if reports_path.exists():
        return reports_path
    return BASE_DIR / file_name


def read_csv_safely(file_name: str) -> pd.DataFrame:
    file_path = resolve_input_file(file_name)
    if not file_path.exists() or file_path.stat().st_size == 0:
        return pd.DataFrame()

    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except Exception as exc:  # pragma: no cover - diagnostic fallback
            last_error = exc
    raise RuntimeError(f"Failed to read {file_path}: {last_error}")


def clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    return text


def to_number(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def text_blob(row: pd.Series) -> str:
    fields = [
        "event_type",
        "event_nature",
        "impact_direction",
        "title_cn",
        "title",
        "summary_cn",
        "summary",
        "country",
        "company",
        "project",
        "resource_type",
    ]
    return " ".join(clean_text(row.get(col, "")) for col in fields).lower()


def choose_urgency(priority_level: str, score: float, impact_level: str) -> str:
    if priority_level == "P1" or score >= 160 or impact_level == "高":
        return "高"
    if priority_level == "P2" or score >= 100 or impact_level == "中":
        return "中"
    return "低"


def choose_deadline(urgency: str) -> str:
    if urgency == "高":
        return "本周内"
    if urgency == "中":
        return "两周内"
    return "持续跟踪"


def choose_decision_type(urgency: str, blob: str) -> str:
    if urgency == "高":
        return "立即决策"
    if any(key in blob for key in ["政策", "出口", "ban", "restriction", "royalty", "tax"]):
        return "风险复核"
    if any(key in blob for key in ["投资", "交易", "offtake", "funding", "acquisition", "stake"]):
        return "投资评估"
    return "持续跟踪"


def choose_owner_team(blob: str) -> str:
    if any(key in blob for key in ["出口", "政策", "ban", "restriction", "royalty", "tax", "许可", "合规", "government"]):
        return "战略/法务"
    if any(key in blob for key in ["供应", "供给", "停产", "减产", "复产", "库存", "shipment", "production"]):
        return "采购"
    if any(key in blob for key in ["投资", "交易", "并购", "offtake", "funding", "acquisition", "stake", "融资"]):
        return "资源投资"
    if any(key in blob for key in ["价格", "期货", "现货", "price"]):
        return "市场/采购"
    return "战略"


def build_action(row: pd.Series, impact_row: pd.Series | None = None) -> dict[str, Any]:
    event_id = clean_text(row.get("event_id", ""))
    priority_level = clean_text(row.get("priority_level", "Watch"), "Watch")
    event_type = clean_text(row.get("event_type", "其他事件"), "其他事件")
    score = to_number(row.get("event_priority_score", 0), 0)
    country = clean_text(row.get("country", ""))
    company = clean_text(row.get("company", ""))
    project = clean_text(row.get("project", row.get("project_name", "")))
    impact_level = ""
    impact_summary = ""
    if impact_row is not None and not impact_row.empty:
        impact_level = clean_text(impact_row.get("impact_level", ""))
        impact_summary = clean_text(impact_row.get("impact_summary", ""))

    blob = text_blob(row)
    urgency = choose_urgency(priority_level, score, impact_level)
    deadline = choose_deadline(urgency)
    owner_team = choose_owner_team(blob)
    decision_type = choose_decision_type(urgency, blob)

    # CATL-oriented rule templates. Keep the wording short enough for dashboard cards.
    if any(key in blob for key in ["出口", "export", "ban", "restriction", "政策收紧", "政策变化"]):
        recommended_action = "更新该国资源风险敞口，复核政策执行范围，暂停新增高风险项目推进。"
        owner_team = "战略/法务"
    elif any(key in blob for key in ["供给收缩", "供应扰动", "停产", "减产", "suspend", "disruption", "strike", "output cut", "guidance cut"]):
        recommended_action = "评估替代资源与采购安全库存，复核未来两周补库窗口和长协覆盖比例。"
        owner_team = "采购"
    elif any(key in blob for key in ["复产", "重启", "restart", "ramp-up", "commissioning", "first production", "commercial production", "扩产"]):
        recommended_action = "将项目纳入持续跟踪清单，复核产量爬坡、现金成本和长协锁量可能性。"
        owner_team = "资源投资"
    elif any(key in blob for key in ["投资", "交易", "offtake", "funding", "acquisition", "stake", "joint venture", "融资"]):
        recommended_action = "评估是否纳入优先接触清单，关注交易结构、估值水平和资源锁定能力。"
        owner_team = "资源投资"
    elif any(key in blob for key in ["审批", "许可", "permit", "approval", "environmental", "lawsuit", "court", "delay"]):
        recommended_action = "要求法务和资源团队复核项目审批路径、执行时间表和投产概率。"
        owner_team = "战略/法务"
    elif any(key in blob for key in ["价格", "price", "期货", "现货", "shortage", "tightness"]):
        recommended_action = "启动价格与采购节奏复盘，结合期现价差、库存天数和长协覆盖比例调整采购策略。"
        owner_team = "市场/采购"
    else:
        recommended_action = "保持事件跟踪，复核对供应安全、采购成本和资源配置节奏的潜在影响。"

    # Add explicit exposure context when available, but avoid making the card too long.
    exposure_bits = [item for item in [country, company, project] if item]
    exposure_text = " / ".join(exposure_bits[:3])
    if exposure_text and urgency == "高":
        recommended_action = f"围绕{exposure_text}，{recommended_action}"

    if impact_summary and urgency == "高" and len(recommended_action) < 70:
        recommended_action = f"{recommended_action} 同步复核CATL影响：{impact_summary[:40]}。"

    trigger_condition = f"{priority_level} / {event_type} / 分数 {score:.0f}"

    return {
        "event_id": event_id,
        "decision_type": decision_type,
        "recommended_action": recommended_action,
        "urgency": urgency,
        "owner_team": owner_team,
        "deadline": deadline,
        "trigger_condition": trigger_condition,
        "status": "待处理",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_published_at": clean_text(row.get("published_at", "")),
        "event_type": event_type,
        "priority_level": priority_level,
        "event_priority_score": score,
    }


def build_weekly_decision_actions() -> pd.DataFrame:
    events_df = read_csv_safely(CRITICAL_EVENTS_FILE)
    impact_df = read_csv_safely(CATL_IMPACT_FILE)
    output_path = REPORTS_DIR / OUTPUT_FILE

    if events_df.empty:
        out = pd.DataFrame(columns=OUTPUT_COLUMNS)
        out.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"No weekly critical events found. Saved empty {output_path}")
        return out

    events_df = events_df.copy()
    if "event_id" not in events_df.columns:
        raise ValueError("weekly_critical_events.csv must contain event_id")

    events_df["event_priority_score"] = pd.to_numeric(
        events_df.get("event_priority_score", 0), errors="coerce"
    ).fillna(0)
    if "published_at" in events_df.columns:
        events_df["published_at_dt"] = pd.to_datetime(events_df["published_at"], errors="coerce", utc=True)
    else:
        events_df["published_at_dt"] = pd.NaT

    impact_lookup: dict[str, pd.Series] = {}
    if not impact_df.empty and "event_id" in impact_df.columns:
        impact_lookup = {
            clean_text(row.get("event_id", "")): row
            for _, row in impact_df.iterrows()
            if clean_text(row.get("event_id", ""))
        }

    rows = []
    seen = set()
    sorted_events = events_df.sort_values(
        ["event_priority_score", "published_at_dt"],
        ascending=[False, False],
        na_position="last",
    )
    for _, row in sorted_events.iterrows():
        event_id = clean_text(row.get("event_id", ""))
        if not event_id or event_id in seen:
            continue
        seen.add(event_id)
        rows.append(build_action(row, impact_lookup.get(event_id)))

    out = pd.DataFrame(rows)
    out = out.reindex(columns=OUTPUT_COLUMNS)
    out.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved {output_path} with {len(out)} rows")
    return out


def main() -> None:
    build_weekly_decision_actions()


if __name__ == "__main__":
    main()
