from datetime import datetime

import math


def fetch_open_source_indicators():
    """
    抓取开源市场变量。
    如果 AkShare 接口失败，则使用基准兜底参数。
    """
    print(f"[{datetime.now()}] Fetching open-source market indicators...")

    try:
        import akshare as ak

        # 这里先保留 LC2609 作为示例，未来可以改成动态主力合约
        try:
            df_futures = ak.futures_zh_spot(subscribe_list="LC2609", market="GFEX")
            if df_futures.empty:
                raise RuntimeError("Empty GFEX spot data")

            if "current_price" in df_futures.columns:
                lithium_futures_price = float(df_futures["current_price"].iloc[0])
            else:
                lithium_futures_price = float(df_futures.iloc[0, -1])

        except Exception:
            df_daily = ak.futures_zh_daily_sina(symbol="LC2609")
            lithium_futures_price = float(df_daily["close"].iloc[-1])

        try:
            df_crude = ak.futures_foreign_hist(symbol="CO")
            crude_oil_price = float(df_crude["close"].iloc[-1])
        except Exception:
            crude_oil_price = 83.5

        print(f"GFEX lithium futures price: {lithium_futures_price}")
        print(f"Crude oil shadow price: {crude_oil_price}")

        return lithium_futures_price, crude_oil_price

    except Exception as exc:
        print(f"Market data fetch failed, using fallback values. Reason: {exc}")
        return 178000.0, 83.5


def _fallback_series(base, step=0.002, periods=6):
    return [round(base * (1 + (idx - periods + 1) * step), 4) for idx in range(periods)]


def _latest_and_change(values):
    clean_values = []

    for value in values:
        try:
            if value is None or math.isnan(float(value)):
                continue
            clean_values.append(float(value))
        except Exception:
            continue

    if not clean_values:
        return 0.0, 0.0, []

    latest = clean_values[-1]
    previous = clean_values[0]
    change_5d = 0.0 if previous == 0 else (latest / previous - 1) * 100

    return latest, change_5d, clean_values


def _extract_numeric_series(df):
    if df is None or getattr(df, "empty", True):
        return []

    candidate_cols = [
        "close",
        "收盘",
        "current_price",
        "最新价",
        "最新",
        "price",
        "现价",
    ]

    for col in candidate_cols:
        if col in df.columns:
            try:
                return df[col].tail(6).astype(float).tolist()
            except Exception:
                continue

    for col in reversed(df.columns):
        try:
            values = df[col].tail(6).astype(float).tolist()
            if values:
                return values
        except Exception:
            continue

    return []


def _make_item(label, values, source):
    latest, change_5d, sparkline = _latest_and_change(values)

    return {
        "label": label,
        "latest": latest,
        "change_5d": change_5d,
        "sparkline": sparkline,
        "source": source,
    }


def _fetch_lc_inventory_item(ak):
    if ak is None:
        return _make_item("碳酸锂库存/仓单", _fallback_series(53885), "Fallback")

    df = ak.futures_inventory_em(symbol="lc")
    values = _extract_numeric_series(df[["库存"]])
    item = _make_item("碳酸锂库存/仓单", values, "东方财富")

    if not df.empty and "增减" in df.columns:
        try:
            latest_change = float(df["增减"].iloc[-1])
            item["change_label"] = f"最新增减 {latest_change:+,.0f} 吨"
        except Exception:
            pass

    item["unit_label"] = "吨"
    return item


def fetch_market_monitor_data():
    """
    Fetch market monitor data through AkShare when available.
    Falls back to stable baseline series so the dashboard remains usable.
    """
    try:
        import akshare as ak
    except Exception:
        ak = None

    def safe_fetch(label, fallback_base, fetchers):
        if ak is not None:
            for fetcher in fetchers:
                try:
                    values = _extract_numeric_series(fetcher(ak))
                    if values:
                        return _make_item(label, values, "AkShare")
                except Exception:
                    continue

        return _make_item(label, _fallback_series(fallback_base), "Fallback")

    commodities = [
        safe_fetch(
            "GFEX碳酸锂",
            178000,
            [
                lambda ak: ak.futures_zh_spot(subscribe_list="LC2609", market="GFEX"),
                lambda ak: ak.futures_zh_daily_sina(symbol="LC2609"),
            ],
        ),
        safe_fetch(
            "铜",
            78500,
            [
                lambda ak: ak.futures_zh_daily_sina(symbol="CU0"),
                lambda ak: ak.futures_zh_spot(subscribe_list="CU0", market="SHFE"),
            ],
        ),
        safe_fetch(
            "镍",
            126000,
            [
                lambda ak: ak.futures_zh_daily_sina(symbol="NI0"),
                lambda ak: ak.futures_zh_spot(subscribe_list="NI0", market="SHFE"),
            ],
        ),
        safe_fetch(
            "原油",
            83.5,
            [
                lambda ak: ak.futures_foreign_hist(symbol="CO"),
            ],
        ),
    ]

    fx = [
        safe_fetch("USD/CNY", 7.20, []),
        safe_fetch("AUD/USD", 0.66, []),
        safe_fetch("CLP/USD", 0.0011, []),
        safe_fetch("ARS/USD", 0.0010, []),
    ]

    equities = [
        safe_fetch("SQM", 42.0, []),
        safe_fetch("ALB", 112.0, []),
        safe_fetch("Pilbara", 3.2, []),
        safe_fetch("MIN", 46.0, []),
        safe_fetch("Arcadium", 5.1, []),
        safe_fetch("赣锋", 31.0, []),
        safe_fetch("天齐", 34.0, []),
    ]

    macro = [
        safe_fetch("DXY", 104.0, []),
        safe_fetch("US10Y", 4.30, []),
        safe_fetch("WTI", 79.0, []),
        safe_fetch("铜价", 78500, []),
    ]

    try:
        inventory = [_fetch_lc_inventory_item(ak)]
    except Exception:
        inventory = [_make_item("碳酸锂库存/仓单", _fallback_series(53885), "Fallback")]

    return {
        "commodities": commodities,
        "inventory": inventory,
        "fx": fx,
        "equities": equities,
        "macro": macro,
    }
