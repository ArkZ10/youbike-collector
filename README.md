# YouBike 2.0 Station Availability Dataset

A self-collected real-time dataset of YouBike 2.0 station status across Taipei City,
built to support supervised machine learning research on bike availability forecasting.

---

## Research Question

**Given the current operational status of a YouBike 2.0 station in Taipei City, how many
bikes will be available at that station 5 hours from now?**

This dataset was constructed to train and evaluate regression models (Random Forest,
XGBoost, LSTM) for predicting future bike availability at the station level.

---

## Dataset Summary

| Attribute               | Value                                             |
|-------------------------|---------------------------------------------------|
| Collection period       | March 22 – March 29, 2026 (8 days)               |
| Total records           | 392,334 rows                                      |
| Stations                | 1,731 active stations                             |
| Districts               | 13 districts of Taipei City                       |
| Average records/station | ~227 per station                                  |
| Polling interval        | Every 10 minutes (via GitHub Actions scheduler)   |
| Actual median interval  | ~47 minutes (verified from timestamp differences) |
| Missing values          | None                                              |
| File                    | `data/youbike_dataset.csv`                        |

> **Note on polling interval:** The GitHub Actions `schedule` trigger has a known
> queuing delay under high load. Although the workflow is scheduled every 10 minutes,
> the actual median gap between consecutive snapshots is ~47 minutes. This is a
> platform limitation, not a code error. Future collections should use a dedicated
> always-on server (e.g., a VPS with a cron job) to guarantee the intended interval.

---

## External Data Source

- **API:** YouBike 2.0 Real-Time Station Data
- **Provider:** Taipei City Government Open Data Platform
- **Endpoint:** `https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json`
- **License:** Open Government Data License, version 1.0 (Taiwan)
- **No authentication required** — the endpoint is publicly accessible

---

## Data Collection Process

### Hardware / Infrastructure

No specialized hardware was required. Collection ran entirely on **GitHub Actions**
free-tier cloud runners (Ubuntu 22.04 virtual machines), triggered automatically on a
cron schedule. No local machine needed to stay online.

### Software

| Tool               | Version | Purpose                                    |
|--------------------|---------|--------------------------------------------|
| Python             | 3.12    | Core scripting language                    |
| `requests`         | 2.31+   | HTTP GET requests to the YouBike API       |
| `csv` (stdlib)     | —       | Appending rows to the output CSV           |
| `datetime` (stdlib)| —       | UTC timestamp injection per snapshot       |
| GitHub Actions     | —       | Automated scheduler (`*/10 * * * *` cron)  |

### Collection Conditions

- Only **active stations** (`is_active = 1`) were recorded; inactive stations were
  skipped at collection time.
- Each poll fetched **all stations simultaneously** in a single API call, so all rows
  within one snapshot share the same UTC timestamp.
- Data was appended to a single growing CSV file. No rows were deleted or filtered
  after collection.
- The dataset spans **both weekdays and weekends** (Sunday March 22 through Sunday
  March 29), capturing different usage patterns across the full weekly cycle.

### How It Works

GitHub Actions runs `collect_one_poll.py` on a `*/10 * * * *` cron schedule, which:

1. Sends a GET request to the YouBike 2.0 API endpoint
2. Parses the JSON response (one object per station)
3. Computes derived fields (`bike_ratio`, `is_empty`, `is_full`, time features)
4. Appends all active-station rows to `data/youbike_dataset.csv`
5. Commits and pushes the updated CSV back to this repository

### Repository Structure

```
youbike-collector/
├── collect_one_poll.py        <- called by GitHub Actions each run
├── collect_youbike.py         <- run locally for continuous collection
├── requirements.txt
├── data/
│   └── youbike_dataset.csv    <- the dataset (grows each run)
└── .github/
    └── workflows/
        └── collect.yml        <- GitHub Actions schedule definition
```

---

## Dataset Fields

| Field             | Type     | Description                                                     |
|-------------------|----------|-----------------------------------------------------------------|
| `timestamp`       | datetime | UTC time of the API snapshot (`YYYY-MM-DD HH:MM:SS`)           |
| `station_id`      | int64    | Unique 9-digit station identifier (e.g., `500101001`)          |
| `station_name`    | string   | Station name in Traditional Chinese                            |
| `area`            | string   | District of Taipei City (13 unique values)                     |
| `available_bikes` | int64    | Number of bikes currently available for rental                 |
| `empty_slots`     | int64    | Number of vacant docking slots                                 |
| `total_docks`     | int64    | Total docking capacity of the station                          |
| `lat`             | float64  | GPS latitude in WGS84                                          |
| `lng`             | float64  | GPS longitude in WGS84                                         |
| `is_active`       | int64    | Service status flag (1 = active; inactive stations excluded)   |
| `is_empty`        | int64    | 1 if `available_bikes <= 2` (near-empty threshold)             |
| `is_full`         | int64    | 1 if `empty_slots <= 2` (near-full threshold)                  |
| `bike_ratio`      | float64  | `available_bikes / total_docks` (rounded to 4 decimal places)  |
| `hour`            | int64    | Hour of day extracted from UTC timestamp (0–23)                |
| `minute`          | int64    | Minute extracted from UTC timestamp (0, 10, 20, ...)           |
| `day_of_week`     | int64    | 0 = Monday, 6 = Sunday                                         |
| `is_weekend`      | int64    | 1 if Saturday or Sunday, else 0                                |

---

## Dataset Example

First snapshot (2026-03-22 03:14 UTC = 11:14 Taiwan time, Sunday morning):

| timestamp           | station_id | area | available_bikes | empty_slots | total_docks | bike_ratio |
|---------------------|------------|------|-----------------|-------------|-------------|------------|
| 2026-03-22 03:14:41 | 500101001  | 大安區 | 26             | 2           | 28          | 0.9286     |
| 2026-03-22 03:14:41 | 500101002  | 大安區 | 20             | 1           | 21          | 0.9524     |
| 2026-03-22 03:14:41 | 500101003  | 大安區 | 6              | 22          | 28          | 0.2143     |
| 2026-03-22 03:14:41 | 500101004  | 大安區 | 1              | 10          | 11          | 0.0909     |
| 2026-03-22 03:14:41 | 500101005  | 大安區 | 3              | 13          | 16          | 0.1875     |

---

## Dataset Composition

| District (area)        | Approx. Stations | Notes                          |
|------------------------|-----------------|--------------------------------|
| 大安區 (Da'an)          | ~180            | Dense residential/commercial   |
| 信義區 (Xinyi)          | ~160            | Business district, Taipei 101  |
| 中山區 (Zhongshan)      | ~150            | Mixed commercial               |
| 松山區 (Songshan)       | ~140            | Transport hub area             |
| 士林區 (Shilin)         | ~130            | Includes night market area     |
| 內湖區 (Neihu)          | ~120            | Tech park (Neihu Science Park) |
| + 7 other districts    | ~851            | Covers all of Taipei City      |

All 1,731 stations were active (`is_active = 1`) for the entire collection period.
No stations dropped in or out during the 8-day window.

---

## Data Quality and Cleanup

- **No missing values** in any field across all 392,334 rows.
- **No duplicate rows** — each `(timestamp, station_id)` pair is unique.
- **No inactive stations** — all were filtered out at collection time.
- **Timestamp consistency** — all rows within a single poll share the same UTC
  timestamp; it is assigned once at the start of each run, not per row.
- **Polling jitter** — the actual polling interval varies between ~40 and ~90 minutes
  due to GitHub Actions scheduling delays. The median is ~47 minutes. This was
  verified by computing per-station timestamp differences in the analysis notebook.

---

## Usage

### Run a single poll manually

```bash
python collect_one_poll.py
```

### Run locally (continuous collection)

```bash
pip install -r requirements.txt
python collect_youbike.py
```

### Stop GitHub Actions collection

Go to: **Actions tab → select workflow → Disable workflow**

---
