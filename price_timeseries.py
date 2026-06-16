from pathlib import Path
from datetime import datetime

import pandas as pd


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = REPORTS_DIR / "lce_price_timeseries.csv"


def load_csv(file_name):
    file_path = REPORTS_DIR / file_name

    if not file_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)
    except Exception:
        return pd.DataFrame()


def get_value(df, col, default=0.0):
    if df.empty or col not in df.columns:
        return default

    try:
        value = df.iloc[0][col]
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def build_lce_price_timeseries():
    """
    历史价格锚定《五矿期货碳酸锂周报 2026/05/23》：
    - 2026/05/22 MMLC现货指数：177725 元/吨
    - 电池级碳酸锂报价：175800-180700 元/吨
    - LC2609短期参考区间：17.5-21万元/吨

    注意：
    由于周报图片中图表没有逐日数据表，本脚本不伪造逐日真实行情。
    历史段采用“文档锚点 + 趋势插值”的方式，显示为文档校准历史曲线。
    """

    document_df = load_csv("document_market_inputs.csv")
    forecast_df = load_csv("lce_price_forecast.csv")

    # 文档真实锚点
    mmlc_spot_price = get_value(document_df, "mmlc_spot_price", 177725)
    battery_low = get_value(document_df, "battery_lce_low", 175800)
    battery_high = get_value(document_df, "battery_lce_high", 180700)
    gfex_lower = get_value(document_df, "short_term_lc2609_lower", 175000)
    gfex_upper = get_value(document_df, "short_term_lc2609_upper", 210000)
    paper_center = get_value(document_df, "paper_price_center", 182000)
    paper_floor = get_value(document_df, "paper_price_floor", 170000)
    paper_defensive = get_value(document_df, "paper_defensive_level", 175000)

    # 预测值
    expected_price = get_value(forecast_df, "expected_lce_price", paper_center)
    forecast_lower = get_value(forecast_df, "lower_bound", gfex_lower)
    forecast_upper = get_value(forecast_df, "upper_bound", gfex_upper)

    if forecast_lower <= 0:
        forecast_lower = gfex_lower

    if forecast_upper <= 0:
        forecast_upper = gfex_upper

    if expected_price <= 0:
        expected_price = paper_center

    rows = []

    # =========================
    # 历史段：2026-01 到 2026-05
    # =========================
    # 这里使用文档锚定插值，而非伪装真实逐日报价。
    # 逻辑：1月接近成本防御线，5月22日锚定177725。
    # =========================

    historical_points = [
        ("2026-01-16", 172500),
        ("2026-02-16", 173800),
        ("2026-03-16", 175200),
        ("2026-04-16", 176500),
        ("2026-05-22", mmlc_spot_price),
    ]

    for date_str, price in historical_points:
        rows.append(
            {
                "date": date_str,
                "actual_lce_price": round(price, 2),
                "forecast_center": None,
                "forecast_lower": None,
                "forecast_upper": None,
                "paper_center": paper_center,
                "paper_floor": paper_floor,
                "paper_defensive": paper_defensive,
                "series_type": "document_calibrated_history",
                "source_note": "历史段以五矿周报2026/05/22 MMLC=177725为锚点进行插值校准",
            }
        )

    # =========================
    # 未来段：未来6个月预测
    # =========================

    forecast_dates = pd.date_range(
        start="2026-06-01",
        end="2027-01-01",
        freq="MS",
    )

    for i, date in enumerate(forecast_dates):
        # 让未来中枢从当前现货向模型预测中枢平滑过渡
        if len(forecast_dates) > 1:
            weight = i / (len(forecast_dates) - 1)
        else:
            weight = 1

        center = mmlc_spot_price * (1 - weight) + expected_price * weight

        # 预测区间从周报短期区间向模型区间平滑过渡
        lower = gfex_lower * (1 - weight) + forecast_lower * weight
        upper = gfex_upper * (1 - weight) + forecast_upper * weight

        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "actual_lce_price": None,
                "forecast_center": round(center, 2),
                "forecast_lower": round(lower, 2),
                "forecast_upper": round(upper, 2),
                "paper_center": paper_center,
                "paper_floor": paper_floor,
                "paper_defensive": paper_defensive,
                "series_type": "model_forecast",
                "source_note": "未来段结合五矿周报17.5-21万元短期区间与模型预测中枢",
            }
        )

    output_df = pd.DataFrame(rows)

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("Saved reports/lce_price_timeseries.csv")
    print(output_df.to_string(index=False))

    return output_df


if __name__ == "__main__":
    build_lce_price_timeseries()
