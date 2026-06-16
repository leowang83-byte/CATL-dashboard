from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    newsapi_key: str
    database_url: str
    news_query: str
    news_language: str
    news_page_size: int
    project_seed_path: Path
    cost_curve_source_path: Path
    log_level: str
    log_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            newsapi_key=os.getenv("NEWSAPI_KEY", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            news_query=os.getenv(
                "NEWS_QUERY",
                "(lithium OR spodumene OR brine) AND (mine OR mining OR project OR carbonate OR hydroxide)",
            ),
            news_language=os.getenv("NEWS_LANGUAGE", "en"),
            news_page_size=int(os.getenv("NEWS_PAGE_SIZE", "100")),
            project_seed_path=Path(os.getenv("PROJECT_SEED_PATH", "config/mining_projects.seed.csv")),
            cost_curve_source_path=Path(os.getenv("COST_CURVE_SOURCE_PATH", "config/cost_curve.seed.csv")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_dir=Path(os.getenv("LOG_DIR", "logs")),
        )

    def validate_for_database(self) -> None:
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")

    def validate_for_news(self) -> None:
        if not self.newsapi_key:
            raise ValueError("NEWSAPI_KEY is required")

