import os
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg", "postgresql+psycopg2")
engine = create_engine(DB_URL)

OUTPUT_DIR = Path(__file__).parent / "data" / "sequences"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_SIZE = 90
ZSCORE_THRESHOLD = 2.0

SEASON_MAP = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
}


def prepare_station(conn, station_id):
    stats = conn.execute(text("""
        SELECT
            AVG(max_air_temp),  STDDEV(max_air_temp),
            AVG(min_air_temp),  STDDEV(min_air_temp),
            AVG(prcp_amt),      STDDEV(prcp_amt)
        FROM observations
        WHERE station_id = :sid AND max_air_temp IS NOT NULL
    """), {"sid": station_id}).fetchone()

    if stats[0] is None or stats[1] is None or stats[1] == 0:
        return

    mean_max, std_max, mean_min, std_min, mean_rain, std_rain = stats
    std_min = std_min or 1.0
    mean_rain = mean_rain if mean_rain is not None else 0.0
    std_rain = std_rain or 1.0

    # Identify normal years — annual mean max_air_temp within 2σ of long-run mean
    annual = conn.execute(text("""
        SELECT EXTRACT(YEAR FROM date)::int AS year, AVG(max_air_temp) AS mean
        FROM observations
        WHERE station_id = :sid AND max_air_temp IS NOT NULL
        GROUP BY year
        HAVING COUNT(*) >= 180
    """), {"sid": station_id}).fetchall()

    normal_years = [
        row[0] for row in annual
        if abs((row[1] - mean_max) / std_max) <= ZSCORE_THRESHOLD
    ]
    if not normal_years:
        return

    years_str = ",".join(str(y) for y in normal_years)
    rows = conn.execute(text(f"""
        SELECT date, max_air_temp, min_air_temp, prcp_amt
        FROM observations
        WHERE station_id = :sid
          AND EXTRACT(YEAR FROM date)::int IN ({years_str})
        ORDER BY date
    """), {"sid": station_id}).fetchall()

    if len(rows) < WINDOW_SIZE:
        return

    # Impute nulls with long-run means, then normalise with global station statistics
    dates = []
    values = []
    for ob_date, max_t, min_t, rain in rows:
        max_t = max_t if max_t is not None else mean_max
        min_t = min_t if min_t is not None else mean_min
        rain = rain if rain is not None else mean_rain
        values.append([
            (max_t - mean_max) / std_max,
            (min_t - mean_min) / std_min,
            (rain - mean_rain) / std_rain,
        ])
        dates.append(ob_date)

    # Slice into 90-day windows and group by season of the first day
    season_windows = {"winter": [], "spring": [], "summer": [], "autumn": []}
    for i in range(len(values) - WINDOW_SIZE + 1):
        season = SEASON_MAP[dates[i].month]
        season_windows[season].append(values[i:i + WINDOW_SIZE])

    for season, windows in season_windows.items():
        if not windows:
            continue
        arr = np.array(windows, dtype=np.float32)  # shape: [N, 90, 3]
        np.save(OUTPUT_DIR / f"station_{station_id}_{season}.npy", arr)
        print(f"  {season}: {arr.shape}")


def main():
    with engine.connect() as conn:
        station_ids = [
            row[0] for row in conn.execute(
                text("SELECT src_id FROM stations ORDER BY src_id")
            ).fetchall()
        ]
        print(f"Processing {len(station_ids)} stations...")
        for i, sid in enumerate(station_ids):
            print(f"[{i+1}/{len(station_ids)}] Station {sid}")
            prepare_station(conn, sid)
    print("Done.")


if __name__ == "__main__":
    main()
