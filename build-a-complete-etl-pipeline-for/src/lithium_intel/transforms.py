from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COUNTRY_PATTERNS = {
    "Argentina": r"\bargentina|jujuy|catamarca|salta\b",
    "Australia": r"\baustralia|western australia|pilbara|greenbushes\b",
    "Brazil": r"\bbrazil|minas gerais\b",
    "Canada": r"\bcanada|quebec|ontario\b",
    "Chile": r"\bchile|atacama\b",
    "China": r"\bchina|jiangxi|sichuan|qinghai\b",
    "Democratic Republic of Congo": r"\bdrc|democratic republic of congo|manono\b",
    "United States": r"\bunited states|usa|nevada|north carolina|california\b",
    "Zimbabwe": r"\bzimbabwe\b",
}

EVENT_KEYWORDS = {
    "permitting": ["permit", "approval", "environmental", "license", "licence"],
    "financing": ["financing", "loan", "debt", "equity", "funding", "investment"],
    "production": ["production", "ramp-up", "restart", "shipment", "output"],
    "disruption": ["strike", "protest", "delay", "suspend", "blockade", "accident", "shutdown"],
    "m_and_a": ["acquisition", "merger", "takeover", "joint venture", "stake"],
    "pricing": ["price", "carbonate", "hydroxide", "contract", "spot"],
}

NEGATIVE_TERMS = ["delay", "strike", "protest", "suspend", "shutdown", "cost overrun", "accident", "blockade"]
POSITIVE_TERMS = ["approval", "financing", "ramp-up", "commission", "record production", "restart", "expansion"]


def normalize_news_article(article: dict[str, Any]) -> dict[str, Any]:
    source = article.get("source") or {}
    title = article.get("title") or ""
    description = article.get("description") or ""
    content = article.get("content") or ""
    text = " ".join([title, description, content])
    published_at = _parse_datetime(article.get("publishedAt"))

    return {
        "source": source.get("name"),
        "author": article.get("author"),
        "title": title,
        "description": description,
        "content": content,
        "url": article.get("url"),
        "image_url": article.get("urlToImage"),
        "published_at": published_at,
        "raw_payload": json.dumps(article),
        "commodity": "lithium",
        "region": None,
        "country": infer_country(text),
        "project_name": infer_project_name(text),
        "event_type": infer_event_type(text),
        "sentiment_score": infer_sentiment(text),
    }


def infer_country(text: str) -> str | None:
    lowered = text.lower()
    for country, pattern in COUNTRY_PATTERNS.items():
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return country
    return None


def infer_project_name(text: str) -> str | None:
    known_projects = [
        "Greenbushes",
        "Pilgangoora",
        "Mt Cattlin",
        "Salar de Atacama",
        "Cauchari-Olaroz",
        "Thacker Pass",
        "Manono",
        "Kathleen Valley",
    ]
    lowered = text.lower()
    for project in known_projects:
        if project.lower() in lowered:
            return project
    return None


def infer_event_type(text: str) -> str | None:
    lowered = text.lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return event_type
    return "market_update"


def infer_sentiment(text: str) -> float:
    lowered = text.lower()
    positives = sum(1 for term in POSITIVE_TERMS if term in lowered)
    negatives = sum(1 for term in NEGATIVE_TERMS if term in lowered)
    raw = positives - negatives
    return max(-1.0, min(1.0, raw / 3))


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

