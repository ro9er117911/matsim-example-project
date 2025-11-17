# Taipei Station Bus & Rail Mini Feed

Synthetic GTFS subset with just enough content to exercise PT mapping alongside the metro sample.
- **Routes**: `TPE_BUS_299` (bus) and `TRA_LOCAL` (rail)
- **Trips**: one trip per direction for each route (total 4)
- **Stops**: pulled from the real gtfs_tw_v5 `stops.txt` to keep coordinates faithful (Taipei Main, Songshan, Ximen, etc.)
- **Calendar**: WEEKDAY + WEEKEND service windows for 2024

Use together with `tp_metro_gtfs_taipei_station` when running the small-area pipeline.
