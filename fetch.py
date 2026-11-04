"""Download hourly page views for Swedish Wikipedia from the public Wikimedia REST API.
Saves each month separately, so a rerun resumes where it stopped, and backs off politely
when the API says "too many requests" (HTTP 429)."""
import time
from pathlib import Path

import pandas as pd
import requests

PROJECT = "sv.wikipedia.org"
START, END = "2024-01-01", "2026-10-01"
MONTHS = Path("data/months")
OUT = Path("data/hourly.csv")
HEADERS = {"User-Agent": "capacity-planning-study/0.1 (github.com/saishyamdontha)"}


def fetch_month(month):
    first = month.strftime("%Y%m%d00")
    last = (month + pd.offsets.MonthEnd(0)).strftime("%Y%m%d23")
    url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/"
           f"{PROJECT}/all-access/user/hourly/{first}/{last}")
    wait = 5
    for attempt in range(8):
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", wait))
            print(f"  rate limited, waiting {retry_after}s (attempt {attempt + 1})")
            time.sleep(retry_after)
            wait = min(wait * 2, 120)
            continue
        r.raise_for_status()
        return [(it["timestamp"], it["views"]) for it in r.json()["items"]]
    raise RuntimeError(f"gave up on {month:%Y-%m} after repeated rate limits")


def main():
    MONTHS.mkdir(parents=True, exist_ok=True)
    for month in pd.date_range(START, END, freq="MS"):
        path = MONTHS / f"{month:%Y-%m}.csv"
        if path.exists():
            print(f"{month:%Y-%m}: already saved")
            continue
        rows = fetch_month(month)
        pd.DataFrame(rows, columns=["ts", "views"]).to_csv(path, index=False)
        print(f"{month:%Y-%m}: {len(rows)} hours")
        time.sleep(3)
    df = pd.concat(pd.read_csv(p) for p in sorted(MONTHS.glob("*.csv")))
    df["ts"] = pd.to_datetime(df["ts"].astype(str), format="%Y%m%d%H")
    df.sort_values("ts").to_csv(OUT, index=False)
    print(f"saved {len(df)} hours to {OUT}")


if __name__ == "__main__":
    main()
