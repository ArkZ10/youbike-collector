# YouBike Dataset Collector 

Automatically collects real-time YouBike station availability data every 10 minutes using GitHub Actions

## Dataset

- **Source:** Taipei YouBike 2.0 Real-Time API (data.gov.tw)
- **Collection period:** 5 days
- **Frequency:** Every 10 minutes
- **Stations:** ~1,000+ Taipei stations per snapshot
- **File:** `data/youbike_dataset.csv`

## Dataset Fields

| Field | Description |
|---|---|
| `timestamp` | UTC time of snapshot |
| `station_id` | Unique station ID |
| `station_name` | Station name (Chinese) |
| `area` | District area |
| `available_bikes` | Number of bikes available |
| `empty_slots` | Number of empty docking slots |
| `total_docks` | Total docking capacity |
| `lat` / `lng` | GPS coordinates |
| `is_empty` | **Label:** 1 if available_bikes ≤ 2 |
| `is_full` | **Label:** 1 if empty_slots ≤ 2 |
| `bike_ratio` | available_bikes / total_docks |
| `hour` | Hour of day (0–23) |
| `minute` | Minute (0 or 10 or 20...) |
| `day_of_week` | 0=Monday, 6=Sunday |
| `is_weekend` | 1 if Saturday or Sunday |

## How It Works

GitHub Actions runs `collect_one_poll.py` every 10 minutes, which:
1. Fetches live data from the YouBike API
2. Appends new rows to `data/youbike_dataset.csv`
3. Commits and pushes the updated CSV back to this repo

## Files

```
youbike-collector/
├── collect_one_poll.py        ← called by GitHub Actions each run
├── collect_youbike.py         ← run locally if preferred
├── requirements.txt
├── data/
│   └── youbike_dataset.csv    ← growing dataset
└── .github/
    └── workflows/
        └── collect.yml        ← GitHub Actions schedule
```

## Usage

### Run locally
```bash
pip install -r requirements.txt
python collect_youbike.py
```

### Stop collection
Disable the workflow in GitHub: Actions tab → select workflow → disable.
