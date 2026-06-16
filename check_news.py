import pandas as pd
from database import load_table


def main():
    print("========== 检查 event_data 数据库新闻 ==========")

    try:
        df = load_table("event_data")
    except Exception as e:
        print("读取 event_data 失败：", e)
        return

    print("event_data rows:", len(df))
    print("columns:", df.columns.tolist())

    if df.empty:
        print("event_data 是空表，说明新闻没有写入。")
        return

    show_cols = [
        "id",
        "title",
        "source",
        "url",
        "keyword",
        "created_at",
        "risk_score",
        "impact_direction",
    ]

    show_cols = [c for c in show_cols if c in df.columns]

    print("\n========== 最近20条新闻 ==========")
    print(df.tail(20)[show_cols].to_string(index=False))

    print("\n========== 最近20条标题 ==========")
    for title in df.tail(20)["title"].tolist():
        print("-", title)


if __name__ == "__main__":
    main()