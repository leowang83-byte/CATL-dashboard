from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from dashboard_data_contract import DATA_REQUIREMENTS, REPORTS_DIR, apply_contract, empty_contract_frame


def read_csv_safe(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.exists():
        return pd.DataFrame(), "missing_file"
    if path.stat().st_size == 0:
        return pd.DataFrame(), "empty_file"

    encodings = ("utf-8-sig", "utf-8", "gbk")
    last_error = ""
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding), "read_ok"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

    return pd.DataFrame(), f"read_error:{last_error}"


def safe_num(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def latest_row(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype="object")
    return df.iloc[-1]


def inventory_signal(inventory_days: float) -> str:
    if inventory_days <= 0:
        return "暂无数据"
    if inventory_days <= 14:
        return "反弹窗口"
    if inventory_days <= 21:
        return "中性观察"
    return "库存压制"


def price_signal(cost_gap_wan: float, inventory_days: float, inventory_change: float) -> str:
    if cost_gap_wan >= 1.0 and 0 < inventory_days <= 25:
        return "偏强验证"
    if cost_gap_wan < 0 or inventory_days >= 30 or inventory_change >= 1000:
        return "偏弱验证"
    return "验证中"


def build_weekly_market_signals(reports_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    weekly_inputs, weekly_status = read_csv_safe(reports_dir / "weekly_price_inputs.csv")
    forecast, forecast_status = read_csv_safe(reports_dir / "lce_price_forecast.csv")
    document_inputs, document_status = read_csv_safe(reports_dir / "document_market_inputs.csv")
    metrics, metrics_status = read_csv_safe(reports_dir / "aisc_dashboard_metrics.csv")

    weekly_inputs, _ = apply_contract(weekly_inputs, "weekly_price_inputs.csv")
    forecast, _ = apply_contract(forecast, "lce_price_forecast.csv")
    document_inputs, _ = apply_contract(document_inputs, "document_market_inputs.csv")
    metrics, _ = apply_contract(metrics, "aisc_dashboard_metrics.csv")

    market_row = latest_row(document_inputs if not document_inputs.empty else weekly_inputs)
    forecast_row = latest_row(forecast)
    updated_at = str(market_row.get("updated_at", "") or forecast_row.get("updated_at", "") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    inventory_days = safe_num(market_row.get("inventory_days", 0))
    inventory_change = safe_num(market_row.get("gfex_inventory_change_tonnes", 0))
    spot_price_wan = safe_num(market_row.get("mmlc_spot_price", 0)) / 10000

    current_lce_price_wan = safe_num(forecast_row.get("expected_lce_price", 0)) / 10000
    if spot_price_wan > 0:
        current_lce_price_wan = spot_price_wan

    strategic_aisc_p90 = 0.0
    if not metrics.empty and {"metric_name", "metric_value"}.issubset(metrics.columns):
        metric_lookup = dict(zip(metrics["metric_name"].astype(str), metrics["metric_value"]))
        strategic_aisc_p90 = safe_num(metric_lookup.get("strategic_aisc_p90_wan", 0))

    cost_gap_wan = current_lce_price_wan - strategic_aisc_p90 if strategic_aisc_p90 > 0 else 0.0
    inv_signal = inventory_signal(inventory_days)
    px_signal = price_signal(cost_gap_wan, inventory_days, inventory_change)

    source_status = {
        "weekly_price_inputs.csv": weekly_status,
        "lce_price_forecast.csv": forecast_status,
        "document_market_inputs.csv": document_status,
        "aisc_dashboard_metrics.csv": metrics_status,
    }
    status_parts = [f"{name}:{status}" for name, status in source_status.items()]
    validation_status = " / ".join([px_signal, inv_signal])

    df = pd.DataFrame(
        [
            {
                "updated_at": updated_at,
                "price_signal": px_signal,
                "inventory_signal": inv_signal,
                "market_validation_status": validation_status,
                "source_files": ";".join(status_parts),
                "inventory_days": inventory_days,
                "gfex_inventory_change_tonnes": inventory_change,
                "current_lce_price_wan": current_lce_price_wan,
                "strategic_aisc_p90_wan": strategic_aisc_p90,
                "cost_gap_wan": cost_gap_wan,
            }
        ]
    )
    df, health = apply_contract(df, "weekly_market_signals.csv")
    return df, health


def normalize_one(file_name: str, reports_dir: Path) -> dict[str, Any]:
    path = reports_dir / file_name
    df, read_status = read_csv_safe(path)
    if read_status in {"missing_file", "empty_file"}:
        df = empty_contract_frame(file_name)

    normalized, health = apply_contract(df, file_name)
    health["read_status"] = read_status
    health["last_modified"] = (
        datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        if path.exists()
        else ""
    )

    should_write = read_status != "read_error" and (
        not path.exists()
        or bool(health.get("notes"))
        or file_name == "weekly_market_signals.csv"
    )
    if should_write:
        reports_dir.mkdir(parents=True, exist_ok=True)
        normalized.to_csv(path, index=False, encoding="utf-8-sig")
        health["written"] = True
        health["last_modified"] = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    else:
        health["written"] = False

    return health


def normalize_dashboard_data(reports_dir: Path = REPORTS_DIR) -> pd.DataFrame:
    reports_dir.mkdir(parents=True, exist_ok=True)
    health_rows: list[dict[str, Any]] = []

    weekly_signal_df, weekly_signal_health = build_weekly_market_signals(reports_dir)
    weekly_signal_path = reports_dir / "weekly_market_signals.csv"
    weekly_signal_df.to_csv(weekly_signal_path, index=False, encoding="utf-8-sig")
    weekly_signal_health["read_status"] = "derived"
    weekly_signal_health["written"] = True
    weekly_signal_health["last_modified"] = datetime.fromtimestamp(weekly_signal_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    for file_name in DATA_REQUIREMENTS:
        if file_name == "weekly_market_signals.csv":
            health_rows.append(weekly_signal_health)
            continue
        try:
            health_rows.append(normalize_one(file_name, reports_dir))
        except Exception as exc:
            health_rows.append(
                {
                    "file_name": file_name,
                    "rows": 0,
                    "columns": 0,
                    "missing_required_columns": "",
                    "is_empty": True,
                    "allow_empty": DATA_REQUIREMENTS[file_name].allow_empty,
                    "critical": DATA_REQUIREMENTS[file_name].critical,
                    "status": "normalize_error",
                    "read_status": f"{type(exc).__name__}: {exc}",
                    "notes": "",
                    "written": False,
                    "last_modified": "",
                }
            )

    health_df = pd.DataFrame(health_rows)
    status_order = [
        "file_name",
        "status",
        "read_status",
        "rows",
        "columns",
        "missing_required_columns",
        "is_empty",
        "allow_empty",
        "critical",
        "written",
        "last_modified",
        "notes",
    ]
    health_df = health_df[[col for col in status_order if col in health_df.columns]]
    health_df.to_csv(reports_dir / "dashboard_data_health.csv", index=False, encoding="utf-8-sig")
    return health_df


def main() -> None:
    health_df = normalize_dashboard_data()
    print("Dashboard data normalization completed.")
    print(f"Reports directory: {REPORTS_DIR}")
    print(f"Files checked: {len(health_df)}")
    problem_df = health_df[health_df["status"].astype(str) != "ok"]
    if problem_df.empty:
        print("All dashboard CSV contracts are OK.")
    else:
        print("Files needing attention:")
        print(problem_df[["file_name", "status", "read_status", "missing_required_columns"]].to_string(index=False))


if __name__ == "__main__":
    main()

