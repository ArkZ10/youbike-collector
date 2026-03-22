"""
collect_youbike.py
==================
Run this locally if you want to collect data from your own laptop.
Polls the YouBike API every 10 minutes and auto-stops after 5 days.

Usage:
    python collect_youbike.py

Author: Yeftha
"""

import requests
import csv
import time
import os
import logging
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

YOUBIKE_URL     = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
OUTPUT_FILE     = "data/youbike_dataset.csv"
POLL_INTERVAL   = 600   # seconds (10 minutes)
COLLECTION_DAYS = 5     # auto-stop after 5 days

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("collector.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────

FIELDNAMES = [
    "timestamp", "station_id", "station_name", "area",
    "available_bikes", "empty_slots", "total_docks",
    "lat", "lng", "is_active",
    "is_empty", "is_full", "bike_ratio",
    "hour", "minute", "day_of_week", "is_weekend",
]

def init_csv():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()
        log.info(f"Created: {OUTPUT_FILE}")
    else:
        log.info(f"Appending to: {OUTPUT_FILE}")

# ─────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────

def fetch_youbike():
    try:
        r = requests.get(YOUBIKE_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        log.info(f"📡 Fetched {len(data)} stations")
        return data
    except requests.RequestException as e:
        log.error(f"Fetch failed: {e}")
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
            log.warning(f"Skipping station {s.get('sno', '?')}: {e}")
            skipped += 1

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerows(rows)

    log.info(f"💾 Saved {len(rows)} rows | Skipped {skipped} inactive")
    return len(rows)

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────

def main():
    start_time = datetime.now()
    end_time   = start_time + timedelta(days=COLLECTION_DAYS)

    log.info("=" * 50)
    log.info("YouBike Collector Started")
    log.info(f"  Start : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  End   : {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  Every : {POLL_INTERVAL // 60} minutes")
    log.info("=" * 50)

    init_csv()
    poll_count = 0

    while datetime.now() < end_time:
        now = datetime.now()
        poll_count += 1
        remaining = str(end_time - now).split(".")[0]
        log.info(f"[Poll #{poll_count}] Remaining: {remaining}")

        stations = fetch_youbike()
        if stations:
            process_and_save(stations, now)
        else:
            log.warning("⚠️  No data — skipping this poll")

        if datetime.now() + timedelta(seconds=POLL_INTERVAL) < end_time:
            log.info(f"💤 Sleeping 10 minutes...")
            time.sleep(POLL_INTERVAL)
        else:
            break

    log.info("=" * 50)
    log.info(f"✅ Done! {poll_count} polls over {COLLECTION_DAYS} days")
    log.info(f"   Saved to: {OUTPUT_FILE}")
    log.info("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("🛑 Stopped manually. Data saved.")