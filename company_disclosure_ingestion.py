from __future__ import annotations

import hashlib
import html
import json
import re
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
OUTPUT_FILE = REPORTS_DIR / "raw_disclosure_events.csv"

OUTPUT_COLUMNS = [
    "event_id",
    "published_at",
    "source",
    "source_type",
    "source_url",
    "company",
    "ticker",
    "exchange",
    "filing_type",
    "announcement_type",
    "title",
    "summary",
    "raw_text",
    "country",
    "project",
    "resource_type",
    "is_price_sensitive",
    "production_guidance_change",
    "capex_change",
    "resource_update",
    "offtake_or_mna",
    "keyword_hit",
    "ingested_at",
]

KEYWORDS = [
    "lithium",
    "spodumene",
    "brine",
    "lithium carbonate",
    "lithium hydroxide",
    "lce",
    "battery metals",
    "critical minerals",
    "mine",
    "production",
    "guidance",
    "shipment",
    "capex",
    "resource",
    "reserve",
    "offtake",
    "acquisition",
    "project",
    "permit",
    "approval",
    "锂",
    "锂矿",
    "锂辉石",
    "盐湖",
    "碳酸锂",
    "氢氧化锂",
    "产量",
    "出货",
    "指引",
    "资本开支",
    "资源量",
    "储量",
    "包销",
    "收购",
    "项目",
    "审批",
    "许可",
]

ANNOUNCEMENT_RULES = [
    (
        "production_guidance",
        ["production guidance", "shipment guidance", "sales guidance", "output", "production", "指引", "产量", "出货", "销量"],
    ),
    (
        "project_update",
        ["project update", "commissioning", "ramp up", "delay", "suspension", "restart", "项目进展", "投产", "爬坡", "延期", "停产", "复产"],
    ),
    (
        "capex_change",
        ["capex", "capital expenditure", "cost increase", "budget", "资本开支", "投资额", "成本上升", "预算"],
    ),
    (
        "resource_update",
        ["resource estimate", "reserve", "mineral resource", "ore reserve", "资源量", "储量", "探明", "推断资源量"],
    ),
    (
        "offtake_or_mna",
        ["offtake", "acquisition", "merger", "divestment", "joint venture", "包销", "收购", "并购", "出售", "合资"],
    ),
    (
        "financial_report",
        ["quarterly report", "annual report", "half-year report", "10-k", "10-q", "6-k", "年报", "季报", "半年报"],
    ),
    (
        "policy_or_legal",
        ["litigation", "regulation", "permit", "license", "approval", "legal", "诉讼", "监管", "审批", "许可", "批准"],
    ),
]

RESOURCE_RULES = {
    "spodumene": ["spodumene", "锂辉石", "hard rock"],
    "brine": ["brine", "salar", "salt lake", "盐湖"],
    "lithium carbonate": ["lithium carbonate", "碳酸锂"],
    "lithium hydroxide": ["lithium hydroxide", "氢氧化锂"],
    "lithium": ["lithium", "lce", "锂"],
}

COUNTRY_RULES = {
    "Australia": ["australia", "pilbara", "wodgina", "greenbushes", "kathleen valley", "澳大利亚", "澳洲"],
    "Chile": ["chile", "atacama", "sqm", "智利"],
    "Argentina": ["argentina", "cauchari", "olaroz", "hombre muerto", "阿根廷"],
    "Zimbabwe": ["zimbabwe", "bikita", "arcadia", "津巴布韦"],
    "Brazil": ["brazil", "grota do cirilo", "巴西"],
    "China": ["china", "chinese", "中国", "赣锋", "天齐", "雅化", "中矿", "盛新", "藏格", "盐湖"],
    "Canada": ["canada", "james bay", "whabouchi", "加拿大"],
    "United States": ["united states", "usa", "thacker pass", "美国"],
    "Ghana": ["ghana", "ewoyaa", "加纳"],
    "DRC": ["drc", "congo", "manono", "刚果"],
}

PROJECT_KEYWORDS = [
    "Atacama",
    "Salar de Atacama",
    "Cauchari-Olaroz",
    "Olaroz",
    "Hombre Muerto",
    "Sal de Vida",
    "Pastos Grandes",
    "Kachi",
    "Rincon",
    "Greenbushes",
    "Pilgangoora",
    "Wodgina",
    "Mt Marion",
    "Kathleen Valley",
    "Finniss",
    "Grota do Cirilo",
    "Ewoyaa",
    "Goulamina",
    "Arcadia",
    "Bikita",
    "Zulu Lithium",
    "James Bay",
    "North American Lithium",
    "Whabouchi",
    "Manono",
    "Thacker Pass",
    "Cinovec",
    "Zinnwald",
]

COMPANIES = [
    {"company": "Albemarle", "ticker": "ALB", "exchange": "NYSE", "country": "United States", "ir_urls": ["https://investors.albemarle.com/news-and-events/news-releases"], "sec_cik": "0000915913"},
    {"company": "SQM", "ticker": "SQM", "exchange": "NYSE/SSE", "country": "Chile", "ir_urls": ["https://ir.sqm.com/English/news/default.aspx"], "sec_cik": "0000901477"},
    {"company": "Pilbara Minerals", "ticker": "PLS", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://www.pilbaraminerals.com.au/news/"]},
    {"company": "Mineral Resources", "ticker": "MIN", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://www.mineralresources.com.au/news-media/"]},
    {"company": "Arcadium Lithium", "ticker": "ALTM", "exchange": "NYSE/ASX", "country": "United States", "ir_urls": ["https://ir.arcadiumlithium.com/news-events/news-releases"], "sec_cik": "0001977303"},
    {"company": "Lithium Americas", "ticker": "LAC", "exchange": "NYSE/TSX", "country": "Canada", "ir_urls": ["https://www.lithiumamericas.com/news"], "sec_cik": "0001440972"},
    {"company": "Sigma Lithium", "ticker": "SGML", "exchange": "NASDAQ/TSXV", "country": "Brazil", "ir_urls": ["https://www.sigmalithiumresources.com/news/"], "sec_cik": "0001848309"},
    {"company": "Allkem", "ticker": "AKE", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://www.allkem.co/investors/announcements/"]},
    {"company": "IGO", "ticker": "IGO", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://www.igo.com.au/site/investor-center/asx-announcements"]},
    {"company": "Liontown Resources", "ticker": "LTR", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://www.ltresources.com.au/investors/asx-announcements/"]},
    {"company": "Core Lithium", "ticker": "CXO", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://corelithium.com.au/investors/asx-announcements/"]},
    {"company": "Sayona Mining", "ticker": "SYA", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://sayonamining.com.au/investors/asx-announcements/"]},
    {"company": "Patriot Battery Metals", "ticker": "PMT", "exchange": "TSX/ASX", "country": "Canada", "ir_urls": ["https://patriotbatterymetals.com/news/"]},
    {"company": "Standard Lithium", "ticker": "SLI", "exchange": "NYSE/TSXV", "country": "United States", "ir_urls": ["https://www.standardlithium.com/investors/news-events/press-releases"], "sec_cik": "0001537137"},
    {"company": "Vulcan Energy Resources", "ticker": "VUL", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://v-er.eu/investors/asx-announcements/"]},
    {"company": "Piedmont Lithium", "ticker": "PLL", "exchange": "NASDAQ/ASX", "country": "United States", "ir_urls": ["https://www.piedmontlithium.com/news/"], "sec_cik": "0001728205"},
    {"company": "Atlantic Lithium", "ticker": "A11", "exchange": "ASX/AIM", "country": "Ghana", "ir_urls": ["https://www.atlanticlithium.com.au/news/"]},
    {"company": "Lake Resources", "ticker": "LKE", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://lakeresources.com.au/investors/asx-announcements/"]},
    {"company": "European Lithium", "ticker": "EUR", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://europeanlithium.com/investors/announcements/"]},
    {"company": "Critical Elements Lithium", "ticker": "CRE", "exchange": "TSXV", "country": "Canada", "ir_urls": ["https://www.cecorp.ca/en/news-releases/"]},
    {"company": "Frontier Lithium", "ticker": "FL", "exchange": "TSXV", "country": "Canada", "ir_urls": ["https://www.frontierlithium.com/news"]},
    {"company": "Neo Lithium", "ticker": "NLC", "exchange": "TSXV", "country": "Canada", "ir_urls": ["https://www.neolithium.ca/news/"]},
    {"company": "Chengxin Lithium", "ticker": "002240", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.cxlithium.com/"]},
    {"company": "AVZ Minerals", "ticker": "AVZ", "exchange": "ASX", "country": "Australia", "ir_urls": ["https://avzminerals.com.au/announcements/"]},
    {"company": "Zijin Mining", "ticker": "601899/2899", "exchange": "SSE/HKEX", "country": "China", "ir_urls": ["https://www.zijinmining.com/investors/announcements.htm"]},
    {"company": "Ganfeng Lithium", "ticker": "002460/1772", "exchange": "SZSE/HKEX", "country": "China", "ir_urls": ["https://www.ganfenglithium.com/news.html"]},
    {"company": "Tianqi Lithium", "ticker": "002466/9696", "exchange": "SZSE/HKEX", "country": "China", "ir_urls": ["https://www.tianqilithium.com/en/news.html"]},
    {"company": "Yahua Group", "ticker": "002497", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.szyahua.com/"]},
    {"company": "Sinomine Resource", "ticker": "002738", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.sinomine.cn/"]},
    {"company": "Chengxin Lithium Group", "ticker": "002240", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.cxlithium.com/"]},
    {"company": "Zangge Mining", "ticker": "000408", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.zanggegf.com/"]},
    {"company": "Qinghai Salt Lake", "ticker": "000792", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.qhyhgf.com/"]},
    {"company": "Yongxing Materials", "ticker": "002756", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.yongxingbxg.com/"]},
    {"company": "Jiangte Motor", "ticker": "002176", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.jiangte.com.cn/"]},
    {"company": "Youngy", "ticker": "002192", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.youngy.com.cn/"]},
    {"company": "Sichuan Energy Power", "ticker": "000155", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.scnyw.com/"]},
    {"company": "Tibet Mineral Development", "ticker": "000762", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.xzkjgf.com/"]},
    {"company": "Tibet Summit Resources", "ticker": "600338", "exchange": "SSE", "country": "China", "ir_urls": ["https://www.xizangzhufeng.com/"]},
    {"company": "Huayou Cobalt", "ticker": "603799", "exchange": "SSE", "country": "China", "ir_urls": ["https://www.huayou.com/"]},
    {"company": "CATL", "ticker": "300750", "exchange": "SZSE", "country": "China", "ir_urls": ["https://www.catl.com/en/news/"]},
    {"company": "BYD", "ticker": "002594/1211", "exchange": "SZSE/HKEX", "country": "China", "ir_urls": ["https://www.bydglobal.com/en/news/index.html"]},
]


def clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_date(value: str) -> str:
    if not value:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return parsedate_to_datetime(value).replace(microsecond=0).isoformat()
    except Exception:
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(parsed):
            return datetime.now().strftime("%Y-%m-%d")
        return parsed.to_pydatetime().replace(microsecond=0).isoformat()


def make_event_id(company: str, title: str, published_at: str, source_url: str) -> str:
    raw = f"{company}|{title}|{published_at}|{source_url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def fetch_url(url: str, timeout: int = 6) -> bytes:
    response = requests.get(
        url,
        timeout=(3, timeout),
        headers={
            "User-Agent": "CATL-Resource-Disclosure-Monitor/1.0 contact: research@example.com",
            "Accept": "application/rss+xml,application/xml,text/html,application/json,*/*",
        },
    )
    response.raise_for_status()
    return response.content


def keyword_hits(*parts: str) -> list[str]:
    blob = " ".join(clean_text(part) for part in parts).lower()
    hits = []
    for keyword in KEYWORDS:
        if keyword.lower() in blob:
            hits.append(keyword)
    return hits


def classify_announcement(*parts: str) -> str:
    blob = " ".join(clean_text(part) for part in parts).lower()
    for label, keywords in ANNOUNCEMENT_RULES:
        if any(keyword.lower() in blob for keyword in keywords):
            return label
    return "other"


def infer_from_rules(*parts: str, rules: dict[str, list[str]]) -> str:
    blob = " ".join(clean_text(part) for part in parts).lower()
    for label, keywords in rules.items():
        if any(keyword.lower() in blob for keyword in keywords):
            return label
    return ""


def infer_project(*parts: str) -> str:
    blob = " ".join(clean_text(part) for part in parts).lower()
    for project in PROJECT_KEYWORDS:
        if project.lower() in blob:
            return project
    return ""


def is_price_sensitive(announcement_type: str, hits: list[str], text: str) -> bool:
    if announcement_type in {
        "production_guidance",
        "project_update",
        "capex_change",
        "resource_update",
        "offtake_or_mna",
        "policy_or_legal",
    }:
        return True
    price_words = ["guidance", "production", "capex", "offtake", "acquisition", "reserve", "产量", "指引", "资本开支", "包销", "收购"]
    text_lower = text.lower()
    return any(word.lower() in text_lower for word in price_words) or any(hit in price_words for hit in hits)


def build_record(
    *,
    company_config: dict,
    source: str,
    source_type: str,
    source_url: str,
    title: str,
    summary: str,
    raw_text: str,
    published_at: str = "",
    filing_type: str = "",
) -> dict | None:
    title = clean_text(title)
    summary = clean_text(summary)
    raw_text = clean_text(raw_text)
    source_url = clean_text(source_url)
    if not title:
        return None

    hits = keyword_hits(title, summary, raw_text, company_config["company"])
    if not hits:
        return None

    published_at = parse_date(published_at)
    announcement_type = classify_announcement(title, summary, raw_text)
    combined_text = " ".join([title, summary, raw_text])

    production_guidance_change = announcement_type == "production_guidance"
    capex_change = announcement_type == "capex_change"
    resource_update = announcement_type == "resource_update"
    offtake_or_mna = announcement_type == "offtake_or_mna"

    return {
        "event_id": make_event_id(company_config["company"], title, published_at, source_url),
        "published_at": published_at,
        "source": source,
        "source_type": source_type,
        "source_url": source_url,
        "company": company_config["company"],
        "ticker": company_config.get("ticker", ""),
        "exchange": company_config.get("exchange", ""),
        "filing_type": filing_type,
        "announcement_type": announcement_type,
        "title": title,
        "summary": summary,
        "raw_text": raw_text or summary or title,
        "country": infer_from_rules(combined_text, company_config.get("country", ""), rules=COUNTRY_RULES) or company_config.get("country", ""),
        "project": infer_project(combined_text),
        "resource_type": infer_from_rules(combined_text, rules=RESOURCE_RULES),
        "is_price_sensitive": is_price_sensitive(announcement_type, hits, combined_text),
        "production_guidance_change": production_guidance_change,
        "capex_change": capex_change,
        "resource_update": resource_update,
        "offtake_or_mna": offtake_or_mna,
        "keyword_hit": "; ".join(sorted(set(hits), key=hits.index)),
        "ingested_at": now_iso(),
    }


def parse_rss(xml_bytes: bytes, company_config: dict, source: str, source_type: str) -> list[dict]:
    records = []
    root = ET.fromstring(xml_bytes)
    for item in root.findall(".//item"):
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        summary = (
            item.findtext("description", default="")
            or item.findtext("summary", default="")
            or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", default="")
        )
        published_at = item.findtext("pubDate", default="") or item.findtext("{http://purl.org/dc/elements/1.1/}date", default="")
        record = build_record(
            company_config=company_config,
            source=source,
            source_type=source_type,
            source_url=link,
            title=title,
            summary=summary,
            raw_text=summary,
            published_at=published_at,
        )
        if record:
            records.append(record)
    return records


def fetch_google_backup(company_config: dict) -> tuple[bool, list[dict], list[str]]:
    company = company_config["company"]
    query = f'"{company}" lithium announcement production guidance project capex offtake'
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        xml_bytes = fetch_url(url)
        return True, parse_rss(xml_bytes, company_config, f"Google News Backup: {company}", "google_news_backup"), []
    except Exception as exc:
        return False, [], [f"{company} google_news_backup failed: {exc}"]


def exchange_query(company_config: dict) -> str:
    company = company_config["company"]
    exchange = company_config.get("exchange", "").upper()
    ticker = company_config.get("ticker", "")
    sites = []
    if "ASX" in exchange:
        sites.append("site:asx.com.au")
    if "HKEX" in exchange:
        sites.append("site:hkexnews.hk")
    if "SZSE" in exchange:
        sites.append("site:szse.cn")
    if "SSE" in exchange:
        sites.append("site:sse.com.cn")
    if "NYSE" in exchange or "NASDAQ" in exchange:
        sites.append("site:sec.gov")
    if not sites:
        return ""
    return f'({" OR ".join(sites)}) "{company}" "{ticker}" lithium announcement disclosure'


def fetch_exchange_backup(company_config: dict) -> tuple[bool, list[dict], list[str]]:
    query = exchange_query(company_config)
    if not query:
        return False, [], []
    company = company_config["company"]
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        xml_bytes = fetch_url(url)
        return True, parse_rss(
            xml_bytes,
            company_config,
            f"Exchange Disclosure Backup: {company}",
            "exchange_disclosure",
        ), []
    except Exception as exc:
        return False, [], [f"{company} exchange_disclosure failed: {exc}"]


def fetch_company_ir(company_config: dict) -> tuple[int, list[dict], list[str]]:
    records = []
    success = 0
    warnings = []
    for url in company_config.get("ir_urls", []):
        try:
            page = fetch_url(url, timeout=5).decode("utf-8", errors="ignore")
            title_match = re.search(r"<title[^>]*>(.*?)</title>", page, flags=re.I | re.S)
            page_title = title_match.group(1) if title_match else f"{company_config['company']} investor relations"
            page_text = clean_text(page)
            record = build_record(
                company_config=company_config,
                source=f"{company_config['company']} Investor Relations",
                source_type="company_ir",
                source_url=url,
                title=page_title,
                summary=page_text[:600],
                raw_text=page_text[:2500],
                published_at="",
            )
            if record:
                records.append(record)
            success += 1
        except Exception as exc:
            warnings.append(f"{company_config['company']} company_ir failed: {exc}")
    return success, records, warnings


def fetch_sec_filings(company_config: dict) -> tuple[bool, list[dict], list[str]]:
    cik = company_config.get("sec_cik")
    if not cik:
        return False, [], []
    cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        data = fetch_url(url, timeout=6)
        payload = json.loads(data.decode("utf-8", errors="ignore"))
        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])[:30]
        dates = recent.get("filingDate", [])[:30]
        accession_numbers = recent.get("accessionNumber", [])[:30]
        primary_docs = recent.get("primaryDocument", [])[:30]
        records = []
        for form, filing_date, accession, primary_doc in zip(forms, dates, accession_numbers, primary_docs):
            title = f"{company_config['company']} SEC filing {form}"
            clean_accession = str(accession).replace("-", "")
            source_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{clean_accession}/{primary_doc}"
            record = build_record(
                company_config=company_config,
                source="SEC EDGAR",
                source_type="sec_filing",
                source_url=source_url,
                title=title,
                summary=f"{company_config['company']} filed {form} on {filing_date}.",
                raw_text=f"{company_config['company']} SEC filing {form} lithium resource investor disclosure.",
                published_at=filing_date,
                filing_type=form,
            )
            if record:
                records.append(record)
        return True, records, []
    except Exception as exc:
        return False, [], [f"{company_config['company']} sec_filing failed: {exc}"]


def fetch_company(company_config: dict) -> tuple[int, list[dict], list[str]]:
    success_count = 0
    records = []
    warnings = []

    ir_success, ir_records, ir_warnings = fetch_company_ir(company_config)
    success_count += ir_success
    records.extend(ir_records)
    warnings.extend(ir_warnings)

    sec_success, sec_records, sec_warnings = fetch_sec_filings(company_config)
    success_count += 1 if sec_success else 0
    records.extend(sec_records)
    warnings.extend(sec_warnings)

    exchange_success, exchange_records, exchange_warnings = fetch_exchange_backup(company_config)
    success_count += 1 if exchange_success else 0
    records.extend(exchange_records)
    warnings.extend(exchange_warnings)

    google_success, google_records, google_warnings = fetch_google_backup(company_config)
    success_count += 1 if google_success else 0
    records.extend(google_records)
    warnings.extend(google_warnings)

    return success_count, records, warnings


def dedupe_records(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    df = pd.DataFrame(records)
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[OUTPUT_COLUMNS].copy()
    df["_published_key"] = df["published_at"].fillna("").astype(str).str.strip()
    df["_url_key"] = df["source_url"].fillna("").astype(str).str.strip().str.lower()
    df["_title_key"] = df["title"].fillna("").astype(str).str.strip().str.lower()
    df["_company_key"] = df["company"].fillna("").astype(str).str.strip().str.lower()

    with_date = df[df["_published_key"] != ""].drop_duplicates(
        subset=["_company_key", "_title_key", "_published_key"],
        keep="first",
    )
    without_date = df[df["_published_key"] == ""].drop_duplicates(
        subset=["_company_key", "_title_key", "_url_key"],
        keep="first",
    )
    df = pd.concat([with_date, without_date], ignore_index=True)
    df = df.drop(columns=["_published_key", "_url_key", "_title_key", "_company_key"])
    return df


def run_ingestion() -> tuple[int, int, int, int, list[str]]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records = []
    warnings = []
    success_sources = 0

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(fetch_company, company) for company in COMPANIES]
        for future in as_completed(futures):
            try:
                source_count, records, source_warnings = future.result()
                success_sources += source_count
                all_records.extend(records)
                warnings.extend(source_warnings)
            except Exception as exc:
                warnings.append(f"company task failed: {exc}")

    raw_count = len(all_records)
    output_df = dedupe_records(all_records)
    deduped_count = len(output_df)
    output_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    return len(COMPANIES), success_sources, raw_count, deduped_count, warnings


def main() -> None:
    company_count, success_sources, raw_count, deduped_count, warnings = run_ingestion()
    for warning in warnings[:30]:
        print(f"warning: {warning}")
    if len(warnings) > 30:
        print(f"warning: 还有 {len(warnings) - 30} 条来源失败信息已省略")
    print(f"抓取公司数量：{company_count}")
    print(f"成功来源数量：{success_sources}")
    print(f"原始公告数量：{raw_count}")
    print(f"去重后公告数量：{deduped_count}")
    print(f"写入 reports/raw_disclosure_events.csv 的数量：{deduped_count}")


if __name__ == "__main__":
    main()
