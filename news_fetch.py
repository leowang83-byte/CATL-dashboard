import requests
import psycopg2

API_KEY = "b5c90c8e024f40f798bfc5c8bf46dbcd"

conn = psycopg2.connect(
    host="localhost",
    database="catl_lithium_system",
    user="postgres",
    password="314122"
)

cur = conn.cursor()

url = f"https://newsapi.org/v2/everything?q=lithium mining OR lithium export OR lithium ban&apiKey={API_KEY}"
response = requests.get(url)
data = response.json()

articles = data["articles"]

keywords = ["ban", "shutdown", "strike", "export", "restriction", "mine", "policy"]

for article in articles[:10]:
    title = article["title"]
    source = article["source"]["name"]
    news_url = article["url"]

    detected_keyword = ""
    for keyword in keywords:
        if keyword.lower() in title.lower():
            detected_keyword = keyword
            break

    cur.execute(
        """
        INSERT INTO event_data (title, source, url, keyword)
        VALUES (%s, %s, %s, %s)
        """,
        (title, source, news_url, detected_keyword)
    )

conn.commit()
cur.close()
conn.close()

print("News inserted into PostgreSQL.")