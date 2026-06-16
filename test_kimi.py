import os
from pathlib import Path
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k2.6")
KIMI_API_URL = os.getenv(
    "KIMI_API_URL",
    "https://api.moonshot.cn/v1/chat/completions",
)

print("KIMI_API_KEY loaded:", bool(KIMI_API_KEY))
print("KIMI_MODEL:", KIMI_MODEL)
print("KIMI_API_URL:", KIMI_API_URL)

headers = {
    "Authorization": f"Bearer {KIMI_API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": KIMI_MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Translate into Chinese: SQM Reports Earnings for the Three Months Ended March 31, 2026",
        }
    ],
    "temperature": 0.1,
    "thinking": {"type": "disabled"},
}

resp = requests.post(
    KIMI_API_URL,
    headers=headers,
    json=payload,
    timeout=30,
)

print("status:", resp.status_code)
print(resp.text[:1000])