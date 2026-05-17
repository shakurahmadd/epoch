"""
Download ERA5 3-hourly data for UK bounding box, 1990-2020.

One request per month, both variables split across two files by CDS:
  - 2m_temperature   (t2m, stepType=instant) → era5_temp_{year}_{mm}.nc
  - total_precipitation (tp, stepType=accum) → era5_precip_{year}_{mm}.nc

CDS returns a ZIP containing both NetCDF files; this script extracts and renames them.
Resume-safe: skips months where era5_temp_{year}_{mm}.nc already exists.
"""

import cdsapi
import sys
import zipfile
import shutil
import tempfile
from pathlib import Path

OUTPUT_DIR = Path("data/era5")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# UK bounding box: N, W, S, E  (1° buffer beyond station extent)
BBOX = [62, -9, 49, 3]

START_YEAR = 1990
END_YEAR = 2020

# 3-hourly timesteps — 8 per day, enough to capture daily max/min/sum
TIMES = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]

DAYS = [f"{d:02d}" for d in range(1, 32)]

# CDS ZIP filenames (stable internal names from the API)
_INSTANT_NAME = "data_stream-oper_stepType-instant.nc"  # temperature
_ACCUM_NAME = "data_stream-oper_stepType-accum.nc"       # precipitation


def _extract_zip(zip_path: Path, year: int, mm: str) -> None:
    """Unzip CDS response and rename the two NetCDFs to clean names."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        src_temp = temp_dir / _INSTANT_NAME
        src_accum = temp_dir / _ACCUM_NAME

        if not src_temp.exists() or not src_accum.exists():
            members = list(temp_dir.iterdir())
            raise RuntimeError(
                f"Unexpected ZIP contents: {[m.name for m in members]}"
            )

        dest_temp = OUTPUT_DIR / f"era5_temp_{year}_{mm}.nc"
        dest_accum = OUTPUT_DIR / f"era5_precip_{year}_{mm}.nc"
        shutil.move(str(src_temp), dest_temp)
        shutil.move(str(src_accum), dest_accum)
        print(f"    extracted → {dest_temp.name}")
        print(f"    extracted → {dest_accum.name}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def download_month(client: cdsapi.Client, year: int, month: int) -> None:
    mm = f"{month:02d}"
    sentinel = OUTPUT_DIR / f"era5_temp_{year}_{mm}.nc"

    if sentinel.exists():
        print(f"  {year}-{mm}: already exists, skipping")
        return

    zip_path = OUTPUT_DIR / f"era5_{year}_{mm}.zip"
    print(f"  {year}-{mm}: requesting...")
    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": ["2m_temperature", "total_precipitation"],
            "year": str(year),
            "month": mm,
            "day": DAYS,
            "time": TIMES,
            "area": BBOX,
            "data_format": "netcdf",
        },
        str(zip_path),
    )
    _extract_zip(zip_path, year, mm)
    zip_path.unlink(missing_ok=True)
    print(f"  {year}-{mm}: done")


def main() -> None:
    years = list(range(START_YEAR, END_YEAR + 1))

    # Single year mode: python download_era5.py 2000
    if len(sys.argv) == 2:
        years = [int(sys.argv[1])]

    client = cdsapi.Client()

    print(f"Downloading ERA5 3-hourly for {years[0]}–{years[-1]}")
    print(f"UK bbox: {BBOX}  |  Output: {OUTPUT_DIR}/\n")

    for year in years:
        for month in range(1, 13):
            try:
                download_month(client, year, month)
            except Exception as exc:
                print(f"  {year}-{month:02d}: FAILED — {exc}", file=sys.stderr)
                continue

    print("\nDone.")


if __name__ == "__main__":
    main()
