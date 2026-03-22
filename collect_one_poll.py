"""
collect_one_poll.py
===================
Called by GitHub Actions every 10 minutes.
Fetches ONE snapshot of YouBike data and appends it to the CSV.

Author: Yeftha
"""

import requests
import csv
import os
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

YOUBIKE_URL = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
OUTPUT_FILE = "data/youbike_dataset.csv"

FIELDNAMES = [
    "timestamp", "station_id", "station_name", "area",
    "available_bikes", "empty_slots", "total_docks",
    "lat", "lng", "is_active",
    "is_empty", "is_full", "bike_ratio",
    "hour", "minute", "day_of_week", "is_weekend",
]

# ─────────────────────────────────────────────
# INIT CSV
# ─────────────────────────────────────────────

def init_csv():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()
        print(f"✅ Created: {OUTPUT_FILE}")
    else:
        print(f"📂 Appending to: {OUTPUT_FILE}")

# ─────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────

def fetch_youbike():
    try:
        r = requests.get(YOUBIKE_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        print(f"📡 Fetched {len(data)} stations")
        return data
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return []

# ─────────────────────────────────────────────
# PROCESS & SAVE
# ─────────────────────────────────────────────

def process_and_save(stations, now):
    rows = []
    skipped = 0

    for s in stations:
        try:
            # Confirmed API field names (Mar 2026)
            bikes  = int(s.get("available_rent_bikes", 0))
            empty  = int(s.get("available_return_bikes", 0))
            total  = int(s.get("Quantity", 1))
            active = s.get("act", "1")       # comes as string "1" or "0"
            lat    = s.get("latitude", "")
            lng    = s.get("longitude", "")

            # Skip inactive stations
            if str(active) != "1":
                skipped += 1
                continue

            rows.append({
                "timestamp":       now.strftime("%Y-%m-%d %H:%M:%S"),
                "station_id":      s.get("sno", ""),
                "station_name":    s.get("sna", ""),
                "area":            s.get("sarea", ""),
                "available_bikes": bikes,
                "empty_slots":     empty,
                "total_docks":     total,
                "lat":             lat,
                "lng":             lng,
                "is_active":       1,
                "is_empty":        1 if bikes <= 2 else 0,
                "is_full":         1 if empty <= 2 else 0,
                "bike_ratio":      round(bikes / total, 4) if total > 0 else 0,
                "hour":            now.hour,
                "minute":          now.minute,
                "day_of_week":     now.weekday(),
                "is_weekend":      1 if now.weekday() >= 5 else 0,
            })
        except Exception as e:
            print(f"⚠️  Skipping station {s.get('sno', '?')}: {e}")
            skipped += 1

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerows(rows)

    print(f"💾 Saved {len(rows)} rows | Skipped {skipped} inactive stations")
    return len(rows)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    now = datetime.utcnow()
    print(f"⏱️  Poll at {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    init_csv()
    stations = fetch_youbike()

    if stations:
        count = process_and_save(stations, now)
        print(f"✅ Done! {count} records saved to {OUTPUT_FILE}")
    else:
        print("⚠️  No data fetched — nothing saved this poll")