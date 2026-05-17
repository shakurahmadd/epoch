"""
Build CNN downscaler training dataset by pairing ERA5 spatial patches with MIDAS observations.

For each station-day where an observation exists:
  X: (2, 5, 5) ERA5 patch centred on the station's nearest grid cell
       channel 0 — daily max t2m (°C), channel 1 — daily total tp (mm)
  y: observed daily max air temperature (°C) at the station

ERA5 units:
  t2m is in Kelvin  → subtract 273.15 for Celsius
  tp is accumulated in metres per 12-hour forecast window → sum 06Z + 18Z, multiply by 1000 for mm

Output:
  data/training/X.npy    shape (N, 2, 5, 5)  float32
  data/training/y.npy    shape (N,)           float32
  data/training/meta.csv station_id, date per sample
"""

import sys
import numpy as np
import pandas as pd
import xarray as xr
import psycopg2
from pathlib import Path

ERA5_DIR = Path("data/era5")
OUT_DIR = Path("data/training")
CKPT_DIR = OUT_DIR / "checkpoints"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CKPT_DIR.mkdir(exist_ok=True)

PATCH = 2          # half-size: patch extends ±2 cells → 5×5
START_YEAR = 1990
END_YEAR = 2020

DB = dict(host="127.0.0.1", port=5432, user="shakur", password="postgres", dbname="epoch")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def load_stations(conn) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT src_id, latitude, longitude FROM stations",
        conn
    )


def load_observations_for_month(conn, year: int, month: int) -> pd.DataFrame:
    """Return all station observations for the given month as a DataFrame indexed by (station_id, date)."""
    q = """
        SELECT station_id, date::date AS date, max_air_temp
        FROM observations
        WHERE EXTRACT(year FROM date) = %s
          AND EXTRACT(month FROM date) = %s
          AND max_air_temp IS NOT NULL
    """
    df = pd.read_sql(q, conn, params=(year, month))
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.set_index(["station_id", "date"])


# ---------------------------------------------------------------------------
# ERA5 grid helpers
# ---------------------------------------------------------------------------

def nearest_idx(values: np.ndarray, target: float) -> int:
    return int(np.argmin(np.abs(values - target)))


def station_grid_indices(lat_vals, lon_vals, stations: pd.DataFrame) -> pd.DataFrame:
    """
    For each station compute (lat_idx, lon_idx) of its nearest ERA5 cell,
    then check a 5×5 patch fits within the grid. Drop stations too close to the edge.
    """
    n_lat, n_lon = len(lat_vals), len(lon_vals)
    rows = []
    for _, row in stations.iterrows():
        li = nearest_idx(lat_vals, row.latitude)
        lo = nearest_idx(lon_vals, row.longitude)
        if li >= PATCH and li < n_lat - PATCH and lo >= PATCH and lo < n_lon - PATCH:
            rows.append({"src_id": row.src_id, "lat_idx": li, "lon_idx": lo})
    return pd.DataFrame(rows).set_index("src_id")


# ---------------------------------------------------------------------------
# ERA5 daily aggregation
# ---------------------------------------------------------------------------

def daily_max_t2m(ds: xr.Dataset) -> tuple[np.ndarray, list]:
    """
    Returns (array, dates) where array has shape (n_days, n_lat, n_lon) in Celsius.
    t2m is instantaneous — daily max = max over 8 timesteps.
    """
    t2m = ds["t2m"]  # (time, lat, lon) in Kelvin
    times = pd.DatetimeIndex(t2m.valid_time.values)
    dates = sorted(set(times.date))

    daily = np.stack(
        [t2m.values[times.date == d].max(axis=0) for d in dates],
        axis=0
    )
    return (daily - 273.15).astype(np.float32), dates


def daily_total_tp(ds: xr.Dataset, dates: list) -> np.ndarray:
    """
    Returns array of shape (n_days, n_lat, n_lon) in mm.
    tp is accumulated per 12-hour forecast window; daily total = tp[06Z] + tp[18Z].
    """
    tp = ds["tp"]  # (time, lat, lon) in metres
    times = pd.DatetimeIndex(tp.valid_time.values)

    mask_06 = times.hour == 6
    mask_18 = times.hour == 18

    tp_06 = tp.values[mask_06]   # (n_days, lat, lon)
    tp_18 = tp.values[mask_18]   # (n_days, lat, lon)

    # Both windows should cover the same calendar days — verify alignment
    days_06 = [t.date() for t in pd.DatetimeIndex(tp.valid_time.values[mask_06])]
    days_18 = [t.date() for t in pd.DatetimeIndex(tp.valid_time.values[mask_18])]

    # Build daily total indexed by date for safe alignment with t2m dates
    tp_by_date = {}
    for i, d in enumerate(days_06):
        tp_by_date[d] = tp_06[i]
    for i, d in enumerate(days_18):
        if d in tp_by_date:
            tp_by_date[d] = tp_by_date[d] + tp_18[i]
        else:
            tp_by_date[d] = tp_18[i]

    daily = np.stack(
        [tp_by_date.get(d, np.zeros_like(tp_06[0])) for d in dates],
        axis=0
    )
    return (daily * 1000).astype(np.float32)  # metres → mm


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_year(conn, stations: pd.DataFrame, year: int) -> None:
    ckpt_X = CKPT_DIR / f"X_{year}.npy"
    ckpt_y = CKPT_DIR / f"y_{year}.npy"
    ckpt_meta = CKPT_DIR / f"meta_{year}.csv"

    if ckpt_X.exists():
        n = np.load(ckpt_X).shape[0]
        print(f"  {year}: checkpoint exists ({n:,} samples), skipping")
        return

    year_X: list[np.ndarray] = []
    year_y: list[float] = []
    year_meta: list[dict] = []

    for month in range(1, 13):
        mm = f"{month:02d}"
        temp_path = ERA5_DIR / f"era5_temp_{year}_{mm}.nc"
        precip_path = ERA5_DIR / f"era5_precip_{year}_{mm}.nc"

        if not temp_path.exists() or not precip_path.exists():
            print(f"  {year}-{mm}: ERA5 files missing, skipping")
            continue

        print(f"  {year}-{mm}: processing...", end=" ", flush=True)

        ds_temp = xr.open_dataset(temp_path)
        ds_precip = xr.open_dataset(precip_path)

        lat_vals = ds_temp.latitude.values
        lon_vals = ds_temp.longitude.values

        t2m_daily, dates = daily_max_t2m(ds_temp)
        tp_daily = daily_total_tp(ds_precip, dates)

        ds_temp.close()
        ds_precip.close()

        grid_idx = station_grid_indices(lat_vals, lon_vals, stations)
        obs = load_observations_for_month(conn, year, month)

        n_samples = 0
        for src_id, idx_row in grid_idx.iterrows():
            li, lo = int(idx_row.lat_idx), int(idx_row.lon_idx)

            for day_i, date in enumerate(dates):
                if (src_id, date) not in obs.index:
                    continue
                obs_temp = obs.loc[(src_id, date), "max_air_temp"]
                if pd.isna(obs_temp):
                    continue

                t2m_patch = t2m_daily[day_i, li-PATCH:li+PATCH+1, lo-PATCH:lo+PATCH+1]
                tp_patch  = tp_daily[day_i,  li-PATCH:li+PATCH+1, lo-PATCH:lo+PATCH+1]

                if t2m_patch.shape != (5, 5) or tp_patch.shape != (5, 5):
                    continue

                year_X.append(np.stack([t2m_patch, tp_patch], axis=0))
                year_y.append(float(obs_temp))
                year_meta.append({"station_id": src_id, "date": str(date)})
                n_samples += 1

        print(f"{n_samples} samples")

    if not year_X:
        print(f"  {year}: no samples, skipping checkpoint")
        return

    np.save(ckpt_X, np.stack(year_X, axis=0))
    np.save(ckpt_y, np.array(year_y, dtype=np.float32))
    pd.DataFrame(year_meta).to_csv(ckpt_meta, index=False)
    print(f"  {year}: checkpoint saved ({len(year_y):,} samples)")


def merge_checkpoints(years: list[int]) -> None:
    all_X, all_y, all_meta = [], [], []
    for year in years:
        ckpt_X = CKPT_DIR / f"X_{year}.npy"
        ckpt_y = CKPT_DIR / f"y_{year}.npy"
        ckpt_meta = CKPT_DIR / f"meta_{year}.csv"
        if not ckpt_X.exists():
            continue
        all_X.append(np.load(ckpt_X))
        all_y.append(np.load(ckpt_y))
        all_meta.append(pd.read_csv(ckpt_meta))

    if not all_X:
        print("No checkpoints found to merge.")
        return

    X = np.concatenate(all_X, axis=0)
    y = np.concatenate(all_y, axis=0)
    meta = pd.concat(all_meta, ignore_index=True)

    np.save(OUT_DIR / "X.npy", X)
    np.save(OUT_DIR / "y.npy", y)
    meta.to_csv(OUT_DIR / "meta.csv", index=False)

    print(f"\nMerged {len(y):,} samples from {len(all_X)} years")
    print(f"  X: {X.shape}  dtype={X.dtype}  size={X.nbytes / 1e6:.1f} MB")
    print(f"  y: min={y.min():.1f}°C  max={y.max():.1f}°C  mean={y.mean():.1f}°C")
    print(f"  → {OUT_DIR}/")


def main() -> None:
    years = list(range(START_YEAR, END_YEAR + 1))
    if len(sys.argv) == 2:
        years = [int(sys.argv[1])]

    conn = psycopg2.connect(**DB)
    stations = load_stations(conn)
    print(f"Loaded {len(stations)} stations from DB\n")

    for year in years:
        process_year(conn, stations, year)

    conn.close()
    print()
    merge_checkpoints(years)


if __name__ == "__main__":
    main()
