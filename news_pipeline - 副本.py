import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from database import get_connection, load_table


# =========================
# 环境变量
# =========================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

print("Loaded .env from:", ENV_PATH)
print("NEWS_API_KEY loaded:", bool(NEWS_API_KEY))


# =========================
# 新闻搜索关键词
# =========================
# 不要只搜 lithium，否则会抓到大量 lithium-ion 消费品新闻。
# 这里聚焦：锂矿、锂盐、锂辉石、政策、出口、价格、项目进度、供应扰动。
# =========================

NEWS_QUERIES = [
    "lithium mining supply disruption",
    "lithium carbonate price supply",
    "spodumene concentrate price",
    "lithium mine production",
    "lithium export ban",
    "lithium mining policy",
    "lithium royalty tax",
    "lithium project permit approval",
    "lithium refinery processing capacity",
    "lithium supply chain mining",
    "critical minerals lithium policy",
    "battery metals lithium mining",

    "Zimbabwe lithium export ban",
    "Chile lithium policy",
    "Argentina lithium brine project",
    "Australia spodumene mine production",
    "Mali lithium project",
    "Ghana lithium project",
    "Canada lithium mine project",
    "United States lithium project permit",

    "SQM lithium production",
    "Albemarle lithium production",
    "Pilbara Minerals spodumene production",
    "Arcadium Lithium project",
    "Sigma Lithium production",
    "Liontown lithium production",
    "Patriot Battery Metals lithium project",
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
    "battery metals",
    "critical minerals",
]

COMPANY_TERMS = [
    "sqm",
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
    "strike",
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
# 国家与项目关键词
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
            "strike",
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


def make_hash(title, url):
    raw = f"{title}|{url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def normalize_title_for_dedupe(title):
    """
    用于去重：去掉大小写、标点、空格差异。
    """
    text = normalize_text(title)
    for ch in [":", ";", ",", ".", "?", "!", "—", "-", "_", "'", '"', "’", "‘", "“", "”", "(", ")", "[", "]"]:
        text = text.replace(ch, " ")
    text = " ".join(text.split())
    return text


def make_title_hash(title):
    normalized = normalize_title_for_dedupe(title)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def translate_title_to_chinese(title):
    """
    使用 OpenAI 将新闻标题翻译成中文。
    如果没有 OPENAI_API_KEY 或请求失败，则返回原英文标题，避免程序中断。
    """
    if not title:
        return ""

    if not OPENAI_API_KEY:
        return title

    try:
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是专业大宗商品和矿业研究翻译助手。请将英文新闻标题翻译成简洁、准确、适合投研看板展示的中文标题。只输出中文标题，不要解释。",
                },
                {
                    "role": "user",
                    "content": title,
                },
            ],
            "temperature": 0.1,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            return title

        data = response.json()
        translated = data["choices"][0]["message"]["content"].strip()

        if not translated:
            return title

        return translated

    except Exception:
        return title


def is_relevant_lithium_resource_news(title, description=""):
    text = f"{normalize_text(title)} {normalize_text(description)}"

    if any(term in text for term in EXCLUDE_TERMS):
        return False

    has_lithium_term = any(term in text for term in REQUIRED_TERMS)
    has_company_term = any(term in text for term in COMPANY_TERMS)
    has_resource_term = any(term in text for term in RESOURCE_TERMS)

    return (has_lithium_term or has_company_term) and has_resource_term


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

    # 兼容旧表：如果 event_data 已经存在，但没有新字段，则自动补齐。
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

    if response.status_code != 200:
        print("NewsAPI error:", response.status_code, response.text[:500])
        return []

    data = response.json()
    return data.get("articles", [])


def insert_event(article, keyword):
    title = article.get("title") or ""
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

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO event_data (
                title,
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
                event_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (
                title,
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
                "title",
                "source",
                "url",
            ]
        )
        out.to_csv(output_file, index=False, encoding="utf-8-sig")
        return out

    display_cols = [
        "created_at",
        "published_at",
        "country",
        "event_type",
        "impact_direction",
        "risk_score",
        "supply_shock",
        "price_shock",
        "title",
        "source",
        "url",
        "keyword",
    ]

    display_cols = [col for col in display_cols if col in df.columns]

    out = df[display_cols].copy()

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
        articles = fetch_news_for_query(
            query=query,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
        )

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