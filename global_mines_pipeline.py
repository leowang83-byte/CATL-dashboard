import time
import requests
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path


# =========================
# 1. 全球重点锂项目种子库
# 注意：这是“重点项目池”，不是全球100%完整矿库
# 后续可以继续扩展、接入 Mindat / USGS / 付费数据库
# =========================

GLOBAL_LITHIUM_PROJECTS = [
    # Australia
    {"name": "Greenbushes", "country": "Australia", "resource_type": "spodumene", "owner": "Talison Lithium", "status": "Operating"},
    {"name": "Pilgangoora", "country": "Australia", "resource_type": "spodumene", "owner": "Pilbara Minerals", "status": "Operating"},
    {"name": "Wodgina", "country": "Australia", "resource_type": "spodumene", "owner": "Mineral Resources / Albemarle", "status": "Operating"},
    {"name": "Mt Marion", "country": "Australia", "resource_type": "spodumene", "owner": "Mineral Resources / Ganfeng", "status": "Operating"},
    {"name": "Kathleen Valley", "country": "Australia", "resource_type": "spodumene", "owner": "Liontown Resources", "status": "Developing"},
    {"name": "Mt Holland", "country": "Australia", "resource_type": "spodumene", "owner": "Covalent Lithium", "status": "Developing"},
    {"name": "Finniss", "country": "Australia", "resource_type": "spodumene", "owner": "Core Lithium", "status": "Operating"},

    # Chile
    {"name": "Salar de Atacama", "country": "Chile", "resource_type": "brine", "owner": "SQM / Albemarle", "status": "Operating"},
    {"name": "Salar de Maricunga", "country": "Chile", "resource_type": "brine", "owner": "Various", "status": "Developing"},

    # Argentina
    {"name": "Hombre Muerto", "country": "Argentina", "resource_type": "brine", "owner": "Various", "status": "Operating"},
    {"name": "Cauchari-Olaroz", "country": "Argentina", "resource_type": "brine", "owner": "Lithium Argentina / Ganfeng", "status": "Operating"},
    {"name": "Olaroz", "country": "Argentina", "resource_type": "brine", "owner": "Arcadium Lithium", "status": "Operating"},
    {"name": "Pastos Grandes", "country": "Argentina", "resource_type": "brine", "owner": "Various", "status": "Developing"},
    {"name": "Sal de Vida", "country": "Argentina", "resource_type": "brine", "owner": "Arcadium Lithium", "status": "Developing"},
    {"name": "Rincon", "country": "Argentina", "resource_type": "brine", "owner": "Rio Tinto", "status": "Developing"},
    {"name": "Kachi", "country": "Argentina", "resource_type": "brine", "owner": "Lake Resources", "status": "Developing"},

    # United States
    {"name": "Silver Peak", "country": "United States", "resource_type": "brine", "owner": "Albemarle", "status": "Operating"},
    {"name": "Thacker Pass", "country": "United States", "resource_type": "clay", "owner": "Lithium Americas", "status": "Developing"},
    {"name": "Smackover Formation", "country": "United States", "resource_type": "brine", "owner": "Various", "status": "Exploration"},

    # Canada
    {"name": "Whabouchi", "country": "Canada", "resource_type": "spodumene", "owner": "Nemaska Lithium", "status": "Developing"},
    {"name": "James Bay", "country": "Canada", "resource_type": "spodumene", "owner": "Arcadium Lithium", "status": "Developing"},
    {"name": "North American Lithium", "country": "Canada", "resource_type": "spodumene", "owner": "Sayona Mining / Piedmont", "status": "Operating"},

    # Africa
    {"name": "Bikita", "country": "Zimbabwe", "resource_type": "spodumene", "owner": "Sinomine", "status": "Operating"},
    {"name": "Arcadia", "country": "Zimbabwe", "resource_type": "spodumene", "owner": "Huayou Cobalt", "status": "Operating"},
    {"name": "Zulu Lithium", "country": "Zimbabwe", "resource_type": "spodumene", "owner": "Premier African Minerals", "status": "Developing"},
    {"name": "Goulamina", "country": "Mali", "resource_type": "spodumene", "owner": "Leo Lithium / Ganfeng", "status": "Developing"},
    {"name": "Manono", "country": "Democratic Republic of Congo", "resource_type": "spodumene", "owner": "AVZ Minerals / Others", "status": "Developing"},
    {"name": "Ewoyaa", "country": "Ghana", "resource_type": "spodumene", "owner": "Atlantic Lithium", "status": "Developing"},

    # Brazil
    {"name": "Grota do Cirilo", "country": "Brazil", "resource_type": "spodumene", "owner": "Sigma Lithium", "status": "Operating"},

    # Europe
    {"name": "Mina do Barroso", "country": "Portugal", "resource_type": "spodumene", "owner": "Savannah Resources", "status": "Developing"},
    {"name": "Cinovec", "country": "Czech Republic", "resource_type": "zinnwaldite", "owner": "European Metals", "status": "Developing"},
    {"name": "Zinnwald", "country": "Germany", "resource_type": "zinnwaldite", "owner": "Zinnwald Lithium", "status": "Developing"},
]


# =========================
# 2. 数据库连接
# =========================

def get_db_config():
    load_dotenv()

    return {
        "host": os.getenv("PGHOST", "127.0.0.1"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
    }


def get_connection():
    return psycopg2.connect(**get_db_config())


# =========================
# 3. 表结构检查
# =========================

def ensure_tables():
    """
    确保 mining_projects 和 cost_curve 表可用。
    如果缺少必要字段，尽量补齐。
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS mining_projects (
                id SERIAL PRIMARY KEY,
                name TEXT,
                country TEXT,
                latitude FLOAT,
                longitude FLOAT,
                resource_type TEXT,
                reserve_tonnes FLOAT,
                annual_capacity FLOAT,
                owner TEXT,
                status TEXT
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS cost_curve (
                id SERIAL PRIMARY KEY,
                project_id INT,
                aisc_cost FLOAT,
                energy_cost FLOAT,
                transport_cost FLOAT
            );
            """)

        conn.commit()


# =========================
# 4. 地理编码：自动获取经纬度
# =========================

def geocode_project(name, country):
    """
    使用 OpenStreetMap Nominatim 免费地理编码。
    注意：免费服务有频率限制，所以这里每次请求 sleep 一下。
    """
    query = f"{name} lithium mine {country}"

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }

    headers = {
        "User-Agent": "catl-lithium-resource-system/1.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        data = response.json()

        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon

    except Exception:
        pass

    return None, None


# =========================
# 5. 估算基础 AISC
# =========================

def estimate_base_aisc(country, resource_type):
    """
    注意：这是模型初始估算，不是正式财报数据。
    后续应使用 WoodMac / S&P / 公司公告替换。
    """
    country_lower = country.lower()
    resource_lower = resource_type.lower()

    if "brine" in resource_lower:
        if country in ["Chile", "Argentina"]:
            return 45000
        return 60000

    if "spodumene" in resource_lower:
        if country == "Australia":
            return 80000
        if country in ["Zimbabwe", "Mali", "Ghana", "Brazil"]:
            return 90000
        if country == "Canada":
            return 95000
        return 100000

    if "clay" in resource_lower:
        return 110000

    if "zinnwaldite" in resource_lower:
        return 120000

    return 100000


def estimate_energy_cost(country, resource_type):
    if country == "Australia":
        return 12000
    if country in ["Zimbabwe", "Mali", "Ghana", "Democratic Republic of Congo"]:
        return 10000
    if "brine" in resource_type.lower():
        return 6000
    return 8000


def estimate_transport_cost(country):
    if country == "China":
        return 2000
    if country in ["Australia", "Brazil"]:
        return 6000
    if country in ["Zimbabwe", "Mali", "Ghana", "Democratic Republic of Congo"]:
        return 9000
    if country in ["Chile", "Argentina"]:
        return 7000
    if country in ["Canada", "United States"]:
        return 8000
    return 8000


# =========================
# 6. 插入 mining_projects 和 cost_curve
# =========================

def project_exists(cur, name, country):
    cur.execute(
        """
        SELECT id FROM mining_projects
        WHERE lower(name) = lower(%s)
        AND lower(country) = lower(%s)
        LIMIT 1;
        """,
        (name, country)
    )
    row = cur.fetchone()
    return row[0] if row else None


def insert_or_update_projects():
    inserted = 0
    updated = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in GLOBAL_LITHIUM_PROJECTS:
                name = item["name"]
                country = item["country"]
                resource_type = item["resource_type"]
                owner = item["owner"]
                status = item["status"]

                existing_id = project_exists(cur, name, country)

                if existing_id:
                    project_id = existing_id
                    cur.execute(
                        """
                        UPDATE mining_projects
                        SET resource_type = %s,
                            owner = %s,
                            status = %s
                        WHERE id = %s;
                        """,
                        (resource_type, owner, status, project_id)
                    )
                    updated += 1
                else:
                    print(f"Geocoding: {name}, {country}")
                    latitude, longitude = geocode_project(name, country)
                    time.sleep(1)

                    cur.execute(
                        """
                        INSERT INTO mining_projects (
                            name,
                            country,
                            latitude,
                            longitude,
                            resource_type,
                            reserve_tonnes,
                            annual_capacity,
                            owner,
                            status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        (
                            name,
                            country,
                            latitude,
                            longitude,
                            resource_type,
                            0,
                            0,
                            owner,
                            status,
                        )
                    )

                    project_id = cur.fetchone()[0]
                    inserted += 1

                # cost_curve 如果没有，则自动补一条初始估算成本
                cur.execute(
                    """
                    SELECT id FROM cost_curve
                    WHERE project_id = %s
                    LIMIT 1;
                    """,
                    (project_id,)
                )
                cost_row = cur.fetchone()

                if not cost_row:
                    aisc = estimate_base_aisc(country, resource_type)
                    energy = estimate_energy_cost(country, resource_type)
                    transport = estimate_transport_cost(country)

                    cur.execute(
                        """
                        INSERT INTO cost_curve (
                            project_id,
                            aisc_cost,
                            energy_cost,
                            transport_cost
                        )
                        VALUES (%s, %s, %s, %s);
                        """,
                        (project_id, aisc, energy, transport)
                    )

        conn.commit()

    return inserted, updated


# =========================
# 7. 导出报告
# =========================

def export_global_projects_report():
    query = """
    SELECT
        m.id,
        m.name,
        m.country,
        m.latitude,
        m.longitude,
        m.resource_type,
        m.owner,
        m.status,
        c.aisc_cost,
        c.energy_cost,
        c.transport_cost
    FROM mining_projects m
    LEFT JOIN cost_curve c
    ON m.id = c.project_id
    ORDER BY m.country, m.name;
    """

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn)

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    output_path = reports_dir / "global_lithium_projects.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return df, output_path


# =========================
# 8. 主程序
# =========================

def main():
    print("====== Global Lithium Mine Auto-Generation Pipeline ======")

    ensure_tables()

    print("1. Inserting / updating global lithium projects...")
    inserted, updated = insert_or_update_projects()

    print(f"Inserted projects: {inserted}")
    print(f"Updated projects: {updated}")

    print("2. Exporting global lithium project report...")
    df, output_path = export_global_projects_report()

    print("")
    print("Global lithium project database generated.")
    print(f"Total projects in report: {len(df)}")
    print(f"Report saved to: {output_path}")
    print("")
    print("Next steps:")
    print("1. Run: python main.py")
    print("2. Run: streamlit run dashboard.py")


if __name__ == "__main__":
    main()