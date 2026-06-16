from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import requests


NEWSAPI_URL = "https://newsapi.org/v2/everything"


class NewsApiClient:
    def __init__(self, api_key: str, timeout_seconds: int = 30) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def fetch_lithium_news(
        self,
        query: str,
        language: str = "en",
        page_size: int = 100,
        lookback_days: int = 1,
    ) -> list[dict[str, Any]]:
        from_dt = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        params = {
            "q": query,
            "language": language,
            "from": from_dt.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "sortBy": "publishedAt",
            "pageSize": min(page_size, 100),
            "apiKey": self.api_key,
        }
        response = requests.get(NEWSAPI_URL, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "ok":
            raise RuntimeError(f"NewsAPI error: {payload}")
        return list(payload.get("articles", []))

