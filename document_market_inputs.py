from pathlib import Path
from datetime import datetime

import pandas as pd


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def build_document_market_inputs():
    """
    数据来源：五矿期货《碳酸锂周报 2026/05/23》
    数据基准日：2026-05-22 / 2026-05-21
    """

    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_report": "五矿期货碳酸锂周报 2026/05/23",
        "source_date": "2026-05-22",

        # 期现价格
        "mmlc_spot_price": 177725,
        "battery_lce_low": 175800,
        "battery_lce_high": 180700,
        "battery_lce_mid": (175800 + 180700) / 2,
        "industrial_lce_low": 172000,
        "industrial_lce_high": 177000,
        "industrial_lce_mid": (172000 + 177000) / 2,
        "gfex_lc2609_price": 184460,
        "battery_trade_basis_avg": -3350,

        # SC6
        "sc6_low_usd_per_tonne": 2670,
        "sc6_high_usd_per_tonne": 2820,
        "sc6_mid_usd_per_tonne": (2670 + 2820) / 2,

        # 库存
        "smm_inventory_tonnes": 100700,
        "inventory_days": 24.7,
        "large_sample_inventory_tonnes": 137300,
        "gfex_registered_receipts_tonnes": 53047,

        # 供给
        "weekly_lce_production_tonnes": 25893,
        "domestic_lce_production_apr_2026": 110030,
        "domestic_lce_production_yoy_apr_2026": 0.491,
        "domestic_lce_production_ytd_yoy_2026": 0.423,

        # 智利出口
        "chile_lce_export_mar_2026": 28555,
        "chile_lce_export_to_china_mar_2026": 18927,

        # 需求
        "china_nev_sales_apr_2026_wan": 134.4,
        "china_nev_sales_ytd_2026_wan": 430.4,
        "china_nev_sales_yoy_apr_2026": 0.097,
        "china_nev_sales_ytd_yoy_2026": 0.001,

        # 电池
        "china_power_ess_battery_output_apr_2026_gwh": 183.9,
        "china_power_ess_battery_output_ytd_2026_gwh": 671.2,
        "china_power_ess_battery_output_yoy_apr_2026": 0.51,
        "china_power_ess_battery_output_ytd_yoy_2026": 0.51,

        # 策略区间
        "short_term_lc2609_lower": 175000,
        "short_term_lc2609_upper": 210000,
        "paper_price_center": 182000,
        "paper_price_floor": 170000,
        "paper_defensive_level": 175000,
    }

    df = pd.DataFrame([data])

    output_file = REPORTS_DIR / "document_market_inputs.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    # 同步生成 weekly_price_inputs.csv，供 price_forecast.py 使用
    weekly_inputs = {
        "updated_at": data["updated_at"],
        "gfex_futures_price": data["gfex_lc2609_price"],
        "sc6_price_index_usd_per_tonne": data["sc6_mid_usd_per_tonne"],
        "sc6_price_index": data["sc6_mid_usd_per_tonne"],
        "inventory_days": data["inventory_days"],
        "mmlc_spot_price": data["mmlc_spot_price"],
        "battery_lce_mid": data["battery_lce_mid"],
        "battery_lce_low": data["battery_lce_low"],
        "battery_lce_high": data["battery_lce_high"],
        "gfex_registered_receipts_tonnes": data["gfex_registered_receipts_tonnes"],
        "smm_inventory_tonnes": data["smm_inventory_tonnes"],
        "weekly_lce_production_tonnes": data["weekly_lce_production_tonnes"],
        "china_power_ess_battery_output_apr_2026_gwh": data["china_power_ess_battery_output_apr_2026_gwh"],
        "china_power_ess_battery_output_yoy_apr_2026": data["china_power_ess_battery_output_yoy_apr_2026"],
        "price_source": data["source_report"],
    }

    weekly_df = pd.DataFrame([weekly_inputs])
    weekly_df.to_csv(
        REPORTS_DIR / "weekly_price_inputs.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("Saved reports/document_market_inputs.csv")
    print("Saved reports/weekly_price_inputs.csv")
    print(df.to_string(index=False))

    return df


if __name__ == "__main__":
    build_document_market_inputs()