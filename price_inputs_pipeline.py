from pathlib import Path
from datetime import datetime

import os
import pandas as pd
from dotenv import load_dotenv

from market_data import fetch_open_source_indicators


REPORTS_DIR = Path("reports")


def safe_float(value, default):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def load_env_defaults():
    """
    从 .env 中读取暂时无法稳定免费自动获取的变量。
    后续你可以把这些变量替换为 SMM / Fastmarkets / Benchmark / Wind 等接口。
    """
    load_dotenv()

    defaults = {
        "SC6_PRICE_INDEX": safe_float(os.getenv("SC6_PRICE_INDEX"), 2745),
        "CATHODE_UTILIZATION": safe_float(os.getenv("CATHODE_UTILIZATION"), 0.72),
        "INVENTORY_DAYS": safe_float(os.getenv("INVENTORY_DAYS"), 24.7),
    }

    return defaults


def build_weekly_price_inputs():
    """
    每周更新价格预测输入变量。
    当前自动项：
    - GFEX lithium futures price
    - crude oil shadow price

    当前配置项：
    - SC6 price index
    - cathode utilization
    - inventory days
    """

    REPORTS_DIR.mkdir(exist_ok=True)

    env_defaults = load_env_defaults()

    try:
        lithium_futures_price, crude_oil_price = fetch_open_source_indicators()
    except Exception as exc:
        print(f"Market data fetch failed, using fallback values. Reason: {exc}")
        lithium_futures_price = 178000
        crude_oil_price = 83.5

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "gfex_futures_price": round(float(lithium_futures_price), 2),
        "crude_oil_price": round(float(crude_oil_price), 2),
        "sc6_price_index": env_defaults["SC6_PRICE_INDEX"],
        "cathode_utilization": env_defaults["CATHODE_UTILIZATION"],
        "inventory_days": env_defaults["INVENTORY_DAYS"],
        "data_quality_note": (
            "GFEX and crude are fetched automatically. "
            "SC6, utilization and inventory are currently config-based inputs."
        ),
    }

    output_df = pd.DataFrame([output])

    output_path = REPORTS_DIR / "weekly_price_inputs.csv"

    output_df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("Weekly price inputs saved to reports/weekly_price_inputs.csv")
    print(output_df.to_string(index=False))

    return output_df


if __name__ == "__main__":
    build_weekly_price_inputs()