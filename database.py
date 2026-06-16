import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv


def get_db_config():
    """
    从 .env 读取 PostgreSQL 连接参数。
    """
    load_dotenv()

    db_config = {
        "host": os.getenv("PGHOST", "127.0.0.1"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
    }

    missing = [key for key, value in db_config.items() if not value]
    if missing:
        raise RuntimeError(f"Missing database config in .env: {missing}")

    return db_config


def get_connection():
    """
    获取 PostgreSQL 连接。
    """
    return psycopg2.connect(**get_db_config())


def load_table(table_name):
    """
    从 PostgreSQL 读取指定表。
    """
    with get_connection() as conn:
        return pd.read_sql_query(f"SELECT * FROM {table_name};", conn)


def load_resource_dataset():
    """
    读取矿山、成本、政策和新闻风险数据。
    """
    mines = load_table("mining_projects")
    costs = load_table("cost_curve")
    policies = load_table("policy_constraints")

    try:
        events = load_table("event_data")
    except Exception:
        events = pd.DataFrame()

    return mines, costs, policies, events


def create_aisc_history_table():
    """
    如果 aisc_history 表不存在，则自动创建。
    """
    create_sql = """
    CREATE TABLE IF NOT EXISTS aisc_history (
        id SERIAL PRIMARY KEY,
        run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        project_id INT,
        project_name TEXT,
        country TEXT,
        resource_type TEXT,
        base_aisc FLOAT,
        realtime_aisc FLOAT,
        delivered_cost FLOAT,
        crude_oil_price FLOAT,
        risk_score FLOAT
    );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()


def save_aisc_history(resource_cost_table, crude_oil_price):
    """
    保存每次运行生成的动态 AISC 数据，用于形成动态时间序列曲线。
    """
    create_aisc_history_table()

    insert_sql = """
    INSERT INTO aisc_history (
        project_id,
        project_name,
        country,
        resource_type,
        base_aisc,
        realtime_aisc,
        delivered_cost,
        crude_oil_price,
        risk_score
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            for _, row in resource_cost_table.iterrows():
                project_id = None

                if "id" in row.index and pd.notna(row["id"]):
                    project_id = int(row["id"])

                cur.execute(
                    insert_sql,
                    (
                        project_id,
                        row.get("name", ""),
                        row.get("country", ""),
                        row.get("resource_type", ""),
                        float(row.get("aisc_cost", 0) or 0),
                        float(row.get("realtime_aisc", 0) or 0),
                        float(row.get("delivered_cost", 0) or 0),
                        float(crude_oil_price or 0),
                        float(row.get("risk_score", 0) or 0),
                    )
                )

        conn.commit()