from __future__ import annotations

from decimal import Decimal
from typing import Any


JURISDICTION_BASE_RISK = {
    "Australia": 0.20,
    "Canada": 0.22,
    "Chile": 0.36,
    "Argentina": 0.42,
    "United States": 0.30,
    "Brazil": 0.38,
    "China": 0.45,
    "Zimbabwe": 0.62,
    "Democratic Republic of Congo": 0.78,
}

STATUS_RISK = {
    "operating": 0.18,
    "ramp-up": 0.36,
    "development": 0.56,
    "care and maintenance": 0.70,
}


def calculate_project_risk(project: dict[str, Any], recent_events: list[dict[str, Any]], cost_row: dict[str, Any] | None) -> dict[str, Any]:
    status = str(project.get("status") or "").lower()
    country = str(project.get("country") or "")
    operational_risk = STATUS_RISK.get(status, 0.50)
    jurisdiction_risk = JURISDICTION_BASE_RISK.get(country, 0.50)
    news_risk = _news_risk(recent_events)
    market_risk = _market_risk(cost_row)

    total = (
        operational_risk * 0.25
        + jurisdiction_risk * 0.25
        + market_risk * 0.20
        + news_risk * 0.30
    )

    return {
        "operational_risk": round(operational_risk, 3),
        "jurisdiction_risk": round(jurisdiction_risk, 3),
        "market_risk": round(market_risk, 3),
        "news_risk": round(news_risk, 3),
        "total_risk": round(total, 3),
        "rationale": {
            "status": project.get("status"),
            "country": country,
            "recent_event_count": len(recent_events),
            "negative_event_count": sum(1 for event in recent_events if _as_float(event.get("sentiment_score")) < 0),
            "cost_percentile": _as_float(cost_row.get("cost_percentile")) if cost_row else None,
        },
    }


def _news_risk(events: list[dict[str, Any]]) -> float:
    if not events:
        return 0.25
    disruption_count = sum(1 for event in events if event.get("event_type") in {"disruption", "permitting"})
    sentiment_drag = sum(max(0.0, -_as_float(event.get("sentiment_score"))) for event in events)
    return min(1.0, 0.20 + disruption_count * 0.15 + sentiment_drag * 0.20)


def _market_risk(cost_row: dict[str, Any] | None) -> float:
    if not cost_row:
        return 0.45
    percentile = _as_float(cost_row.get("cost_percentile"))
    return min(1.0, max(0.10, percentile))


def _as_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)

