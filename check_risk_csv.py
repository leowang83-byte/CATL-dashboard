from pathlib import Path
import pandas as pd


file_path = Path("reports") / "country_event_risk.csv"

if not file_path.exists():
    print("没有找到 reports/country_event_risk.csv")
else:
    df = pd.read_csv(file_path)
    print("country_event_risk rows:", len(df))
    print("columns:", df.columns.tolist())
    print(df.head(20).to_string(index=False))