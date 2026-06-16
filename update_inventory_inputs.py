from datetime import datetime
from pathlib import Path
import os
import re

import pandas as pd
from pypdf import PdfReader


REPORTS_DIR = Path("reports")
PDF_FILE_NAME = "1781356831981004065.pdf"


def get_default_pdf_path():
    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    candidates = [
        Path(r"E:\桌面\碳酸锂") / PDF_FILE_NAME,
        desktop / "碳酸锂" / PDF_FILE_NAME,
    ]

    for path in candidates:
        if path.exists():
            return path

    return candidates[0]


def to_tonnes(value, unit):
    number = float(str(value).replace(",", ""))
    if unit == "万吨":
        return int(round(number * 10000))
    return int(round(number))


def extract_inventory_from_pdf(pdf_path):
    reader = PdfReader(str(pdf_path))
    text = " ".join((page.extract_text() or "") for page in reader.pages)
    text = " ".join(text.split())

    date_match = re.search(r"(\d{1,2})月(\d{1,2})日，据SMM周度库存报", text)
    inventory_date = ""
    if date_match:
        month = int(date_match.group(1))
        day = int(date_match.group(2))
        inventory_date = f"2026-{month:02d}-{day:02d}"

    smm_match = re.search(
        r"据SMM周度库存报\s*([0-9,]+(?:\.[0-9]+)?)\s*(万吨|吨)",
        text,
    )
    days_match = re.search(r"碳酸锂库存天数约\s*([0-9]+(?:\.[0-9]+)?)\s*天", text)
    large_sample_match = re.search(
        r"大样本周度\s*库存报\s*([0-9,]+(?:\.[0-9]+)?)\s*(万吨|吨)",
        text,
    )
    pdf_receipts_match = re.search(r"注册仓单\s*([0-9,]+)\s*吨", text)

    if not days_match:
        raise ValueError("Could not extract inventory_days from PDF")

    return {
        "source_report": "五矿期货碳酸锂周报 2026/06",
        "source_date": inventory_date,
        "inventory_days": float(days_match.group(1)),
        "smm_inventory_tonnes": (
            to_tonnes(smm_match.group(1), smm_match.group(2)) if smm_match else None
        ),
        "large_sample_inventory_tonnes": (
            to_tonnes(large_sample_match.group(1), large_sample_match.group(2))
            if large_sample_match
            else None
        ),
        "pdf_gfex_registered_receipts_tonnes": (
            int(pdf_receipts_match.group(1).replace(",", "")) if pdf_receipts_match else None
        ),
    }


def fetch_eastmoney_lc_inventory():
    import akshare as ak

    df = ak.futures_inventory_em(symbol="lc")
    if df.empty:
        raise RuntimeError("Eastmoney LC inventory returned empty data")

    latest = df.tail(1).iloc[0]
    return {
        "gfex_inventory_date": str(latest["日期"]),
        "gfex_registered_receipts_tonnes": int(float(latest["库存"])),
        "gfex_inventory_change_tonnes": int(float(latest["增减"])),
    }


def update_csv_row(path, updates):
    if path.exists():
        df = pd.read_csv(path)
        if df.empty:
            df = pd.DataFrame([{}])
    else:
        df = pd.DataFrame([{}])

    row = df.iloc[-1].copy()
    for key, value in updates.items():
        if value is not None:
            row[key] = value

    row["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = pd.DataFrame([row])
    output.to_csv(path, index=False, encoding="utf-8-sig")
    return output


def main():
    REPORTS_DIR.mkdir(exist_ok=True)

    pdf_path = get_default_pdf_path()
    pdf_data = extract_inventory_from_pdf(pdf_path)

    try:
        exchange_data = fetch_eastmoney_lc_inventory()
        exchange_source = "东方财富期货库存数据 lc"
    except Exception as exc:
        exchange_data = {
            "gfex_inventory_date": pdf_data.get("source_date"),
            "gfex_registered_receipts_tonnes": pdf_data.get(
                "pdf_gfex_registered_receipts_tonnes"
            ),
            "gfex_inventory_change_tonnes": None,
        }
        exchange_source = f"PDF fallback; Eastmoney failed: {exc}"

    updates = {
        **pdf_data,
        **exchange_data,
        "inventory_source": "五矿期货周报PDF",
        "exchange_inventory_source": exchange_source,
        "price_source": pdf_data["source_report"],
    }

    document_updates = updates.copy()
    weekly_updates = {
        "inventory_days": updates["inventory_days"],
        "smm_inventory_tonnes": updates["smm_inventory_tonnes"],
        "large_sample_inventory_tonnes": updates["large_sample_inventory_tonnes"],
        "gfex_registered_receipts_tonnes": updates[
            "gfex_registered_receipts_tonnes"
        ],
        "gfex_inventory_date": updates["gfex_inventory_date"],
        "gfex_inventory_change_tonnes": updates["gfex_inventory_change_tonnes"],
        "inventory_source": updates["inventory_source"],
        "exchange_inventory_source": updates["exchange_inventory_source"],
        "price_source": updates["price_source"],
    }

    document_df = update_csv_row(
        REPORTS_DIR / "document_market_inputs.csv",
        document_updates,
    )
    weekly_df = update_csv_row(
        REPORTS_DIR / "weekly_price_inputs.csv",
        weekly_updates,
    )

    print("Inventory inputs updated.")
    print("PDF:", pdf_path)
    print(document_df.to_string(index=False))
    print(weekly_df.to_string(index=False))


if __name__ == "__main__":
    main()
