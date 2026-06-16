import os
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

try:
    import argostranslate.translate
except Exception:
    argostranslate = None

from database import get_connection, load_table


# =========================
# 环境变量
# =========================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TRANSLATOR_PROVIDER = os.getenv("TRANSLATOR_PROVIDER", "argos").lower()

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

print("Loaded .env from:", ENV_PATH)
print("NEWS_API_KEY loaded:", bool(NEWS_API_KEY))
print("TRANSLATOR_PROVIDER:", TRANSLATOR_PROVIDER)


# =========================
# 新闻搜索关键词
# =========================
# 注意：NewsAPI 免费账户容易触发 429。
# 建议先保留 5-8 个高价值关键词，稳定后再扩展。
# =========================

NEWS_QUERIES = [
    "lithium carbonate price supply",
    "spodumene concentrate price",
    "lithium mine production",
    "Chile lithium policy",
    "Australia spodumene production",
    "Zimbabwe lithium export ban",
    "Argentina lithium brine project",
    "SQM lithium production",
]


# =========================
# 相关性过滤词
# =========================

REQUIRED_TERMS = [
    "lithium",
    "spodumene",
    "lithium carbonate",
    "lithium hydroxide",
    "brine",
    "lce",
]

BROAD_MINERAL_TERMS = [
    "critical minerals",
    "battery metals",
    "rare earths",
]

COMPANY_TERMS = [
    "sqm",
    "sociedad quimica",
    "sociedad química",
    "albemarle",
    "pilbara minerals",
    "pilbara",
    "arcadium",
    "lithium argentina",
    "lithium americas",
    "sigma lithium",
    "liontown",
    "minres",
    "mineral resources",
    "igo",
    "tianqi",
    "ganfeng",
    "allkem",
    "patriot battery metals",
    "core lithium",
    "sayona",
    "atlantic lithium",
    "leo lithium",
    "firefinch",
    "savannah resources",
    "zhejiang huayou",
    "zijin",
    "catl",
]

RESOURCE_TERMS = [
    "mine",
    "mining",
    "project",
    "production",
    "supply",
    "export",
    "permit",
    "royalty",
    "tax",
    "policy",
    "ban",
    "shipment",
    "concentrate",
    "carbonate",
    "price",
    "spodumene",
    "brine",
    "refinery",
    "processing",
    "commissioning",
    "ramp-up",
    "restart",
    "suspension",
    "government",
    "environmental",
    "approval",
    "operation",
    "capacity",
    "ore",
    "resource",
    "reserve",
    "guidance",
    "output",
    "production guidance",
    "supply chain",
    "critical minerals",
    "offtake",
    "acquisition",
    "investment",
    "dfs",
    "feasibility",
    "earnings",
    "quarter",
    "results",
]

EXCLUDE_TERMS = [
    "cordless",
    "drill",
    "impact driver",
    "battery deal",
    "lawn mower",
    "robot",
    "vacuum",
    "phone",
    "laptop",
    "power bank",
    "slickdeals",
    "coupon",
    "discount",
    "sale",
    "portable",
    "charger",
    "consumer",
    "gadget",
    "music",
    "album",
    "movie",
    "game",
    "homekit",
    "switchbot",
    "verizon",
    "lexus",
    "suv",
    "e-bike",
    "ebike",
    "astronomers",
    "mediterranean",
    "fertilizer",
    "data center",
    "camera",
    "headphones",
    "smartphone",
    "tablet",
    "tool kit",
    "appliance",
]


# =========================
# 国家关键词
# =========================

COUNTRY_KEYWORDS = {
    "China": [
        "china",
        "chinese",
        "jiangxi",
        "yichun",
        "qinghai",
        "sichuan",
        "tibet",
        "hunan",
        "jiangsu",
        "ganfeng",
        "tianqi",
        "catl",
        "huayou",
        "zijin",
    ],
    "Zimbabwe": [
        "zimbabwe",
        "harare",
        "bikita",
        "arcadia",
        "zulu lithium",
    ],
    "Chile": [
        "chile",
        "chilean",
        "atacama",
        "sqm",
        "salar de atacama",
        "corfo",
    ],
    "Argentina": [
        "argentina",
        "cauchari",
        "olaroz",
        "hombre muerto",
        "salta",
        "jujuy",
        "catamarca",
        "rincon",
    ],
    "Australia": [
        "australia",
        "australian",
        "pilbara",
        "greenbushes",
        "wodgina",
        "pilgangoora",
        "mt marion",
        "mount marion",
        "kathleen valley",
        "liontown",
        "minres",
        "mineral resources",
        "igo",
    ],
    "Canada": [
        "canada",
        "quebec",
        "ontario",
        "james bay",
        "whabouchi",
        "north american lithium",
        "patriot battery metals",
        "sayona",
    ],
    "United States": [
        "united states",
        "u.s.",
        "usa",
        "nevada",
        "thacker pass",
        "clayton valley",
        "lithium americas",
    ],
    "Brazil": [
        "brazil",
        "minas gerais",
        "grota do cirilo",
        "sigma lithium",
    ],
    "Mali": [
        "mali",
        "goulamina",
        "leo lithium",
    ],
    "Ghana": [
        "ghana",
        "ewoyaa",
        "atlantic lithium",
    ],
    "Portugal": [
        "portugal",
        "barroso",
        "mina do barroso",
        "savannah resources",
    ],
    "Czech Republic": [
        "czech",
        "cinovec",
    ],
}


# =========================
# 事件类型识别
# =========================

EVENT_TYPE_RULES = [
    {
        "event_type": "export_ban_or_restriction",
        "terms": [
            "export ban",
            "export restriction",
            "ban exports",
            "ore export",
            "raw lithium export",
        ],
        "risk_score": 0.95,
        "impact_direction": "negative",
        "supply_shock": 0.08,
        "price_shock": 0.06,
    },
    {
        "event_type": "tax_or_royalty_increase",
        "terms": [
            "royalty",
            "tax increase",
            "higher tax",
            "mining tax",
            "windfall tax",
        ],
        "risk_score": 0.80,
        "impact_direction": "negative",
        "supply_shock": 0.03,
        "price_shock": 0.03,
    },
    {
        "event_type": "permit_or_environmental_delay",
        "terms": [
            "permit delay",
            "environmental approval",
            "lawsuit",
            "court",
            "blocked",
            "suspended approval",
            "licence delay",
            "license delay",
        ],
        "risk_score": 0.75,
        "impact_direction": "negative",
        "supply_shock": 0.04,
        "price_shock": 0.03,
    },
    {
        "event_type": "production_disruption",
        "terms": [
            "production disruption",
            "suspend production",
            "suspension",
            "workers strike",
            "miner strike",
            "miners strike",
            "labour strike",
            "labor strike",
            "strike action",
            "industrial action",
            "fire",
            "accident",
            "lower production",
            "cut output",
            "guidance cut",
            "output cut",
            "delay ramp-up",
        ],
        "risk_score": 0.85,
        "impact_direction": "negative",
        "supply_shock": 0.06,
        "price_shock": 0.05,
    },
    {
        "event_type": "project_delay",
        "terms": [
            "project delay",
            "delayed project",
            "postpone",
            "defer",
            "capex delay",
            "funding delay",
            "construction delay",
        ],
        "risk_score": 0.70,
        "impact_direction": "negative",
        "supply_shock": 0.03,
        "price_shock": 0.025,
    },
    {
        "event_type": "price_pressure",
        "terms": [
            "lithium price rises",
            "lithium prices rise",
            "carbonate price rises",
            "spodumene price rises",
            "supply tightness",
            "market tightness",
            "shortage",
        ],
        "risk_score": 0.65,
        "impact_direction": "negative",
        "supply_shock": 0.02,
        "price_shock": 0.04,
    },
    {
        "event_type": "project_approval_or_rampup",
        "terms": [
            "permit approved",
            "approval",
            "commissioning",
            "ramp-up",
            "restart",
            "expansion",
            "increase production",
            "record production",
            "new capacity",
            "first production",
            "commercial production",
        ],
        "risk_score": 0.25,
        "impact_direction": "positive",
        "supply_shock": -0.02,
        "price_shock": -0.02,
    },
    {
        "event_type": "critical_minerals_partnership",
        "terms": [
            "critical minerals deal",
            "critical minerals agreement",
            "critical minerals framework",
            "supply chain agreement",
            "minerals partnership",
            "strategic minerals partnership",
            "framework agreement",
            "strike critical minerals deal",
            "strike a critical minerals deal",
        ],
        "risk_score": 0.30,
        "impact_direction": "positive",
        "supply_shock": 0.0,
        "price_shock": 0.0,
    },
    {
        "event_type": "investment_or_offtake",
        "terms": [
            "funding",
            "investment",
            "offtake",
            "strategic partnership",
            "joint venture",
            "acquisition",
            "stake",
        ],
        "risk_score": 0.30,
        "impact_direction": "positive",
        "supply_shock": -0.01,
        "price_shock": -0.01,
    },
]

DEFAULT_EVENT_TYPE = "general_lithium_resource_news"


# =========================
# 基础工具函数
# =========================

def normalize_text(value):
    if value is None:
        return ""
    return str(value).lower()


def clean_title(title):
    if not title:
        return ""

    title = str(title)
    title = re.sub(r"\s+[-|]\s+[^-|]{2,60}$", "", title).strip()
    title = " ".join(title.split())

    return title


def make_hash(title, url):
    raw = f"{title}|{url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def normalize_title_for_dedupe(title):
    text = normalize_text(clean_title(title))

    for ch in [
        ":", ";", ",", ".", "?", "!", "—", "-", "_", "'", '"',
        "’", "‘", "“", "”", "(", ")", "[", "]", "{", "}", "|", "/"
    ]:
        text = text.replace(ch, " ")

    text = " ".join(text.split())
    text = text.replace("highlights", "")
    text = text.replace("transcript", "")
    text = text.replace("earnings call", "earnings")
    text = " ".join(text.split())

    return text


def make_title_hash(title):
    normalized = normalize_title_for_dedupe(title)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def translate_title_to_chinese(title):
    """
    使用 Argos Translate 本地离线翻译英文新闻标题。
    如果本地模型未安装或翻译失败，则返回原英文标题，避免程序中断。
    """
    if not title:
        return ""

    title = clean_title(title)

    if TRANSLATOR_PROVIDER != "argos":
        return title

    try:
        import argostranslate.translate

        translated = argostranslate.translate.translate(
            title,
            "en",
            "zh",
        )

        if not translated:
            return title

        return translated.strip()

    except Exception as exc:
        print("Argos translation failed:", exc)
        return title


def is_relevant_lithium_resource_news(title, description=""):
    text = f"{normalize_text(title)} {normalize_text(description)}"

    if any(term in text for term in EXCLUDE_TERMS):
        return False

    has_direct_lithium = any(term in text for term in REQUIRED_TERMS)
    has_company_term = any(term in text for term in COMPANY_TERMS)
    has_resource_term = any(term in text for term in RESOURCE_TERMS)
    has_broad_mineral = any(term in text for term in BROAD_MINERAL_TERMS)

    if has_direct_lithium and has_resource_term:
        return True

    if has_company_term and has_resource_term:
        return True

    # 泛关键矿产新闻，只有同时出现锂关键词或锂公司时才保留
    if has_broad_mineral and (has_direct_lithium or has_company_term):
        return True

    return False


def detect_country(title, description=""):
    text = f"{normalize_text(title)} {normalize_text(description)}"

    matched_countries = []

    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                matched_countries.append(country)
                break

    if not matched_countries:
        return "Global"

    return matched_countries[0]


def classify_event(title, description=""):
    text = f"{normalize_text(title)} {normalize_text(description)}"

    for rule in EVENT_TYPE_RULES:
        for term in rule["terms"]:
            if term in text:
                return {
                    "event_type": rule["event_type"],
                    "risk_score": rule["risk_score"],
                    "impact_direction": rule["impact_direction"],
                    "supply_shock": rule["supply_shock"],
                    "price_shock": rule["price_shock"],
                }

    return {
        "event_type": DEFAULT_EVENT_TYPE,
        "risk_score": 0.35,
        "impact_direction": "neutral",
        "supply_shock": 0.0,
        "price_shock": 0.0,
    }


# =========================
# 数据库
# =========================

def ensure_event_data_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS event_data (
            id SERIAL PRIMARY KEY,
            title TEXT,
            title_cn TEXT,
            source TEXT,
            url TEXT UNIQUE,
            keyword TEXT,
            country TEXT,
            published_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            risk_score FLOAT,
            impact_direction TEXT,
            event_type TEXT,
            supply_shock FLOAT,
            price_shock FLOAT,
            event_hash TEXT UNIQUE,
            title_hash TEXT
        );
        """
    )

    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS title TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS title_cn TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS source TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS url TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS keyword TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS country TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS published_at TIMESTAMP NULL;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS risk_score FLOAT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS impact_direction TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS event_type TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS supply_shock FLOAT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS price_shock FLOAT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS event_hash TEXT;")
    cur.execute("ALTER TABLE event_data ADD COLUMN IF NOT EXISTS title_hash TEXT;")

    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_event_data_url_unique ON event_data (url);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_event_data_title_hash ON event_data (title_hash);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_event_data_country ON event_data (country);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_event_data_event_type ON event_data (event_type);")

    conn.commit()
    cur.close()
    conn.close()


# =========================
# NewsAPI 抓取
# =========================

def fetch_news_for_query(query, from_date, to_date):
    if not NEWS_API_KEY:
        raise RuntimeError("NEWS_API_KEY 未配置，请检查 C:\\lithium_news_system\\.env 文件。")

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 30,
        "apiKey": NEWS_API_KEY,
    }

    response = requests.get(url, params=params, timeout=20)

    if response.status_code == 429:
        print("NewsAPI rate limited: 今日免费额度已用完，停止后续新闻抓取。")
        raise RuntimeError("NEWSAPI_RATE_LIMITED")

    if response.status_code != 200:
        print("NewsAPI error:", response.status_code, response.text[:500])
        return []

    data = response.json()
    return data.get("articles", [])


def title_already_exists(cur, title_hash):
    cur.execute(
        """
        SELECT id FROM event_data
        WHERE title_hash = %s
        LIMIT 1;
        """,
        (title_hash,),
    )
    return cur.fetchone() is not None


def insert_event(article, keyword):
    raw_title = article.get("title") or ""
    title = clean_title(raw_title)
    description = article.get("description") or ""
    url = article.get("url") or ""
    source = (article.get("source") or {}).get("name", "")
    published_at = article.get("publishedAt")

    if not title or not url:
        return False

    if not is_relevant_lithium_resource_news(title, description):
        return False

    country = detect_country(title, description)
    event_info = classify_event(title, description)

    event_hash = make_hash(title, url)
    title_hash = make_title_hash(title)
    title_cn = translate_title_to_chinese(title)

    conn = get_connection()
    cur = conn.cursor()

    try:
        if title_already_exists(cur, title_hash):
            conn.rollback()
            return False

        cur.execute(
            """
            INSERT INTO event_data (
                title,
                title_cn,
                source,
                url,
                keyword,
                country,
                published_at,
                risk_score,
                impact_direction,
                event_type,
                supply_shock,
                price_shock,
                event_hash,
                title_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (
                title,
                title_cn,
                source,
                url,
                keyword,
                country,
                published_at,
                event_info["risk_score"],
                event_info["impact_direction"],
                event_info["event_type"],
                event_info["supply_shock"],
                event_info["price_shock"],
                event_hash,
                title_hash,
            ),
        )

        inserted = cur.rowcount > 0
        conn.commit()

    except Exception as e:
        print("Insert error:", e)
        conn.rollback()
        inserted = False

    finally:
        cur.close()
        conn.close()

    return inserted


# =========================
# 输出：国家风险表
# =========================

def build_country_event_risk():
    try:
        df = load_table("event_data")
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        out = pd.DataFrame(
            columns=[
                "country",
                "event_risk_score",
                "event_count",
                "negative_event_count",
                "latest_event_title",
                "latest_event_title_cn",
                "latest_event_type",
                "total_supply_shock",
                "total_price_shock",
            ]
        )
        out.to_csv(REPORTS_DIR / "country_event_risk.csv", index=False, encoding="utf-8-sig")
        return out

    for col, default in [
        ("country", "Global"),
        ("risk_score", 0.35),
        ("impact_direction", "neutral"),
        ("event_type", DEFAULT_EVENT_TYPE),
        ("supply_shock", 0.0),
        ("price_shock", 0.0),
        ("title_cn", ""),
    ]:
        if col not in df.columns:
            df[col] = default

    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0.35)
    df["supply_shock"] = pd.to_numeric(df["supply_shock"], errors="coerce").fillna(0.0)
    df["price_shock"] = pd.to_numeric(df["price_shock"], errors="coerce").fillna(0.0)

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df = df.sort_values("created_at")
    else:
        df["created_at"] = pd.Timestamp.now()

    rows = []

    for country, group in df.groupby("country"):
        event_count = len(group)
        negative_event_count = int((group["impact_direction"] == "negative").sum())

        avg_risk = group["risk_score"].mean()
        max_risk = group["risk_score"].max()

        event_risk_score = round(min(0.95, 0.6 * avg_risk + 0.4 * max_risk), 2)

        latest = group.iloc[-1]

        rows.append(
            {
                "country": country,
                "event_risk_score": event_risk_score,
                "event_count": event_count,
                "negative_event_count": negative_event_count,
                "latest_event_title": latest.get("title", ""),
                "latest_event_title_cn": latest.get("title_cn", ""),
                "latest_event_type": latest.get("event_type", DEFAULT_EVENT_TYPE),
                "total_supply_shock": round(group["supply_shock"].sum(), 4),
                "total_price_shock": round(group["price_shock"].sum(), 4),
            }
        )

    out = pd.DataFrame(rows)

    if not out.empty:
        out = out.sort_values("event_risk_score", ascending=False)

    out.to_csv(
        REPORTS_DIR / "country_event_risk.csv",
        index=False,
        encoding="utf-8-sig",
    )

    return out


# =========================
# 输出：新闻事件明细表
# =========================

def build_news_event_summary():
    try:
        df = load_table("event_data")
    except Exception:
        df = pd.DataFrame()

    output_file = REPORTS_DIR / "news_event_summary.csv"

    if df.empty:
        out = pd.DataFrame(
            columns=[
                "created_at",
                "published_at",
                "country",
                "event_type",
                "impact_direction",
                "risk_score",
                "supply_shock",
                "price_shock",
                "title_cn",
                "title",
                "source",
                "url",
                "keyword",
                "title_hash",
            ]
        )
        out.to_csv(output_file, index=False, encoding="utf-8-sig")
        return out

    for col, default in [
        ("title_cn", ""),
        ("title_hash", ""),
        ("event_type", DEFAULT_EVENT_TYPE),
        ("impact_direction", "neutral"),
        ("risk_score", 0.35),
        ("supply_shock", 0.0),
        ("price_shock", 0.0),
    ]:
        if col not in df.columns:
            df[col] = default

    missing_cn_mask = df["title_cn"].isna() | (df["title_cn"].astype(str).str.strip() == "")
    if missing_cn_mask.any() and "title" in df.columns:
        df.loc[missing_cn_mask, "title_cn"] = df.loc[missing_cn_mask, "title"].apply(
            translate_title_to_chinese
        )

    display_cols = [
        "created_at",
        "published_at",
        "country",
        "event_type",
        "impact_direction",
        "risk_score",
        "supply_shock",
        "price_shock",
        "title_cn",
        "title",
        "source",
        "url",
        "keyword",
        "title_hash",
    ]

    display_cols = [col for col in display_cols if col in df.columns]

    out = df[display_cols].copy()

    if "title_hash" in out.columns and out["title_hash"].astype(str).str.len().gt(0).any():
        out = out.drop_duplicates(subset=["title_hash"], keep="first")
    elif "title_cn" in out.columns:
        out = out.drop_duplicates(subset=["title_cn"], keep="first")
    elif "title" in out.columns:
        out = out.drop_duplicates(subset=["title"], keep="first")

    if "created_at" in out.columns:
        out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")
        out = out.sort_values("created_at", ascending=False)

    out.to_csv(output_file, index=False, encoding="utf-8-sig")

    return out


# =========================
# 主程序
# =========================

def main():
    ensure_event_data_table()

    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=7)

    print("News search window:", from_date, "to", to_date)

    total_fetched = 0
    total_relevant = 0
    total_inserted = 0

    for query in NEWS_QUERIES:
        try:
            articles = fetch_news_for_query(
                query=query,
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat(),
            )
        except RuntimeError as exc:
            if str(exc) == "NEWSAPI_RATE_LIMITED":
                print("检测到 NewsAPI 限流，提前结束新闻抓取。")
                break
            raise

        print("Query:", query, "Fetched:", len(articles))
        total_fetched += len(articles)

        for article in articles:
            title = article.get("title") or ""
            description = article.get("description") or ""

            if is_relevant_lithium_resource_news(title, description):
                total_relevant += 1

            if insert_event(article, query):
                total_inserted += 1

    print("Fetched articles:", total_fetched)
    print("Relevant articles:", total_relevant)
    print("Inserted new articles into event_data:", total_inserted)

    risk_df = build_country_event_risk()
    summary_df = build_news_event_summary()

    print("Saved reports/country_event_risk.csv")
    print(risk_df.to_string(index=False))

    print("Saved reports/news_event_summary.csv")
    print(summary_df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()