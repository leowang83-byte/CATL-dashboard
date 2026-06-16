from __future__ import annotations

import hashlib
import html
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_FILE = REPORTS_DIR / "raw_news_events.csv"

GOOGLE_NEWS_KEYWORDS = [
    "lithium mine shutdown",
    "lithium production guidance",
    "lithium export ban",
    "lithium royalty tax",
    "spodumene mine delay",
    "lithium offtake agreement",
    "lithium brine project approval",
    "Argentina lithium policy",
    "Chile lithium royalty",
    "Zimbabwe lithium export ban",
    "Pilbara lithium production",
    "SQM lithium production",
    "Albemarle lithium guidance",
    "Ganfeng lithium project",
    "Tianqi lithium project",
]

MINING_RSS_URLS = [
    "https://www.mining.com/feed/",
]

COMPANY_NEWS_SOURCES = [
    {
        "company": "Albemarle",
        "url": "https://www.albemarle.com/news",
        "keywords": ["lithium", "guidance", "production", "project"],
    },
    {
        "company": "SQM",
        "url": "https://www.sqm.com/en/news/",
        "keywords": ["lithium", "production", "brine", "salar"],
    },
    {
        "company": "Pilbara Minerals",
        "url": "https://www.pilbaraminerals.com.au/news/",
        "keywords": ["lithium", "spodumene", "production", "offtake"],
    },
    {
        "company": "Mineral Resources",
        "url": "https://www.mineralresources.com.au/news-media/",
        "keywords": ["lithium", "spodumene", "production", "guidance"],
    },
    {
        "company": "Arcadium Lithium",
        "url": "https://arcadiumlithium.com/news/",
        "keywords": ["lithium", "brine", "carbonate", "hydroxide"],
    },
    {
        "company": "Lithium Americas",
        "url": "https://www.lithiumamericas.com/news",
        "keywords": ["lithium", "approval", "permit", "project"],
    },
    {
        "company": "Sigma Lithium",
        "url": "https://www.sigmalithiumresources.com/news/",
        "keywords": ["lithium", "production", "spodumene", "shipment"],
    },
    {
        "company": "Ganfeng Lithium",
        "url": "https://www.ganfenglithium.com/news.html",
        "keywords": ["lithium", "project", "carbonate", "hydroxide"],
    },
    {
        "company": "Tianqi Lithium",
        "url": "https://www.tianqilithium.com/en/news.html",
        "keywords": ["lithium", "project", "spodumene", "carbonate"],
    },
]

FILTER_KEYWORDS = [
    "lithium",
    "spodumene",
    "brine",
    "lce",
    "lithium carbonate",
    "lithium hydroxide",
    "battery metals",
    "critical minerals",
    "mine",
    "shutdown",
    "suspension",
    "production",
    "guidance",
    "royalty",
    "tax",
    "export",
    "ban",
    "restriction",
    "offtake",
    "acquisition",
    "permit",
    "approval",
    "锂",
    "锂矿",
    "碳酸锂",
    "氢氧化锂",
    "锂辉石",
    "盐湖",
    "停产",
    "减产",
    "出口限制",
    "资源税",
    "矿业税",
    "审批",
    "许可",
    "包销",
    "收购",
]

COUNTRY_KEYWORDS = {
    "Argentina": ["argentina", "阿根廷"],
    "Chile": ["chile", "智利"],
    "Zimbabwe": ["zimbabwe", "津巴布韦"],
    "Australia": ["australia", "aussie", "澳大利亚", "澳洲"],
    "Brazil": ["brazil", "巴西"],
    "China": ["china", "chinese", "中国"],
    "Canada": ["canada", "加拿大"],
    "United States": ["united states", "usa", "u.s.", "美国"],
    "Bolivia": ["bolivia", "玻利维亚"],
}

COMPANY_KEYWORDS = {
    "Albemarle": ["albemarle"],
    "SQM": ["sqm", "sociedad química", "sociedad quimica"],
    "Pilbara Minerals": ["pilbara minerals", "pilbara"],
    "Mineral Resources": ["mineral resources", "minres"],
    "Arcadium Lithium": ["arcadium"],
    "Lithium Americas": ["lithium americas"],
    "Sigma Lithium": ["sigma lithium"],
    "Ganfeng Lithium": ["ganfeng", "赣锋"],
    "Tianqi Lithium": ["tianqi", "天齐"],
}

RESOURCE_TYPE_KEYWORDS = {
    "spodumene": ["spodumene", "hard rock", "锂辉石"],
    "brine": ["brine", "salar", "salt lake", "盐湖"],
    "lithium carbonate": ["lithium carbonate", "碳酸锂"],
    "lithium hydroxide": ["lithium hydroxide", "氢氧化锂"],
    "lithium": ["lithium", "lce", "锂"],
}


def clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_event_id(title: str, source_url: str, source: str = "") -> str:
    raw = f"{title}|{source_url}|{source}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).replace(microsecond=0).isoformat()
    except Exception:
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(parsed):
            return ""
        return parsed.to_pydatetime().replace(microsecond=0).isoformat()


def fetch_url(url: str, timeout: int = 6) -> bytes:
    response = requests.get(
        url,
        timeout=(3, timeout),
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    return response.content


def keyword_hits(*parts: str) -> list[str]:
    blob = " ".join(clean_text(part) for part in parts).lower()
    hits = []
    for keyword in FILTER_KEYWORDS:
        if keyword.lower() in blob:
            hits.append(keyword)
    return hits


def infer_by_keywords(blob: str, mapping: dict[str, list[str]]) -> str:
    blob = blob.lower()
    for label, keywords in mapping.items():
        if any(keyword.lower() in blob for keyword in keywords):
            return label
    return ""


def build_record(
    *,
    published_at: str,
    source: str,
    source_url: str,
    title: str,
    summary: str,
    raw_text: str,
    keyword_source: str = "",
    company_hint: str = "",
) -> dict | None:
    title = clean_text(title)
    summary = clean_text(summary)
    raw_text = clean_text(raw_text)
    source_url = clean_text(source_url)
    if not title or not source_url:
        return None

    hits = keyword_hits(title, summary, raw_text, keyword_source)
    if not hits:
        return None

    blob = " ".join([title, summary, raw_text, keyword_source])
    company = company_hint or infer_by_keywords(blob, COMPANY_KEYWORDS)
    return {
        "event_id": make_event_id(title, source_url, source),
        "published_at": published_at,
        "source": clean_text(source),
        "source_url": source_url,
        "title": title,
        "summary": summary,
        "raw_text": raw_text or summary or title,
        "country": infer_by_keywords(blob, COUNTRY_KEYWORDS),
        "company": company,
        "project": "",
        "resource_type": infer_by_keywords(blob, RESOURCE_TYPE_KEYWORDS),
        "keyword_hit": "; ".join(sorted(set(hits), key=hits.index)),
        "ingested_at": now_iso(),
    }


def parse_rss_items(xml_bytes: bytes, source_name: str, keyword_source: str = "") -> list[dict]:
    records = []
    root = ET.fromstring(xml_bytes)
    channel_items = root.findall(".//item")
    atom_items = root.findall("{http://www.w3.org/2005/Atom}entry")

    for item in channel_items:
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        summary = (
            item.findtext("description", default="")
            or item.findtext("summary", default="")
            or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", default="")
        )
        published_at = parse_datetime(
            item.findtext("pubDate", default="")
            or item.findtext("{http://purl.org/dc/elements/1.1/}date", default="")
        )
        record = build_record(
            published_at=published_at,
            source=source_name,
            source_url=link,
            title=title,
            summary=summary,
            raw_text=summary,
            keyword_source=keyword_source,
        )
        if record:
            records.append(record)

    for item in atom_items:
        title = item.findtext("{http://www.w3.org/2005/Atom}title", default="")
        link_node = item.find("{http://www.w3.org/2005/Atom}link")
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        summary = item.findtext("{http://www.w3.org/2005/Atom}summary", default="")
        published_at = parse_datetime(
            item.findtext("{http://www.w3.org/2005/Atom}published", default="")
            or item.findtext("{http://www.w3.org/2005/Atom}updated", default="")
        )
        record = build_record(
            published_at=published_at,
            source=source_name,
            source_url=link,
            title=title,
            summary=summary,
            raw_text=summary,
            keyword_source=keyword_source,
        )
        if record:
            records.append(record)
    return records


def fetch_rss_source(url: str, source_name: str, keyword_source: str = "") -> list[dict]:
    try:
        xml_bytes = fetch_url(url)
        return parse_rss_items(xml_bytes, source_name, keyword_source)
    except Exception:
        return []


def fetch_google_news() -> tuple[int, list[dict]]:
    jobs = []
    for keyword in GOOGLE_NEWS_KEYWORDS:
        url = "https://news.google.com/rss/search?q=" f"{quote_plus(keyword)}&hl=en-US&gl=US&ceid=US:en"
        jobs.append((url, f"Google News RSS: {keyword}", keyword))

    records = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_rss_source, *job) for job in jobs]
        for future in as_completed(futures):
            records.extend(future.result())
    return len(jobs), records


def fetch_mining_rss() -> tuple[int, list[dict]]:
    records = []
    jobs = [
        (url, "Mining.com RSS", "mining.com lithium battery metals critical minerals")
        for url in MINING_RSS_URLS
    ]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_rss_source, *job) for job in jobs]
        for future in as_completed(futures):
            records.extend(future.result())
    return len(MINING_RSS_URLS), records


def extract_page_candidates(page_text: str, source_url: str, company: str) -> list[dict]:
    text = clean_text(page_text)
    candidates = []
    title_patterns = re.findall(r"<title[^>]*>(.*?)</title>", page_text, flags=re.I | re.S)
    if title_patterns:
        record = build_record(
            published_at="",
            source=f"{company} company news",
            source_url=source_url,
            title=title_patterns[0],
            summary=text[:500],
            raw_text=text[:1500],
            keyword_source=company,
            company_hint=company,
        )
        if record:
            candidates.append(record)
    return candidates


def fetch_company_pages() -> tuple[int, list[dict]]:
    records = []
    def fetch_company(config: dict) -> list[dict]:
        try:
            page = fetch_url(config["url"], timeout=5).decode("utf-8", errors="ignore")
            return extract_page_candidates(page, config["url"], config["company"])
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = [executor.submit(fetch_company, config) for config in COMPANY_NEWS_SOURCES]
        for future in as_completed(futures):
            records.extend(future.result())
    return len(COMPANY_NEWS_SOURCES), records


def dedupe_records(records: list[dict]) -> pd.DataFrame:
    columns = [
        "event_id",
        "published_at",
        "source",
        "source_url",
        "title",
        "summary",
        "raw_text",
        "country",
        "company",
        "project",
        "resource_type",
        "keyword_hit",
        "ingested_at",
    ]
    if not records:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(records)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df = df[columns].copy()
    df["_dedupe_title"] = df["title"].astype(str).str.strip().str.lower()
    df["_dedupe_url"] = df["source_url"].astype(str).str.strip().str.lower()
    df = df.drop_duplicates(subset=["_dedupe_title", "_dedupe_url"], keep="first")
    df = df.drop(columns=["_dedupe_title", "_dedupe_url"])
    return df


def run_ingestion() -> tuple[int, int, int, int]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    source_total = 0
    records = []

    google_sources, google_records = fetch_google_news()
    source_total += google_sources
    records.extend(google_records)

    mining_sources, mining_records = fetch_mining_rss()
    source_total += mining_sources
    records.extend(mining_records)

    company_sources, company_records = fetch_company_pages()
    source_total += company_sources
    records.extend(company_records)

    fetched_count = len(records)
    output_df = dedupe_records(records)
    deduped_count = len(output_df)
    output_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    written_count = len(output_df)
    return source_total, fetched_count, deduped_count, written_count


def main() -> None:
    source_total, fetched_count, deduped_count, written_count = run_ingestion()
    print(f"抓取来源数量：{source_total}")
    print(f"抓取新闻数量：{fetched_count}")
    print(f"去重后数量：{deduped_count}")
    print(f"写入 reports/raw_news_events.csv 的数量：{written_count}")


if __name__ == "__main__":
    main()
