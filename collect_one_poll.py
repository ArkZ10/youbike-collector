def process_and_save(stations, now):
    rows = []
    for s in stations:
        try:
            # ── Updated field names for new API format ──
            bikes  = int(s.get("available_rent_bikes", s.get("sbi", 0)))
            empty  = int(s.get("available_return_bikes", s.get("bemp", 0)))
            total  = int(s.get("Quantity", s.get("tot", 1)))
            active = int(s.get("act", 1))
            lat    = s.get("latitude",  s.get("lat", ""))
            lng    = s.get("longitude", s.get("lng", ""))

            if not active:
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
                "is_active":       active,
                "is_empty":        1 if bikes <= 2 else 0,
                "is_full":         1 if empty <= 2 else 0,
                "bike_ratio":      round(bikes / total, 4) if total > 0 else 0,
                "hour":            now.hour,
                "minute":          now.minute,
                "day_of_week":     now.weekday(),
                "is_weekend":      1 if now.weekday() >= 5 else 0,
            })
        except Exception as e:
            print(f"⚠️  Skipping station: {e}")

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerows(rows)
    return len(rows)