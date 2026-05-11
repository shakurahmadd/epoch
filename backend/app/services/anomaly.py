import os
import numpy as np
import torch
from pathlib import Path
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.location import get_coordinates, get_nearest_station

MODELS_DIR = Path(os.getenv("MODELS_DIR", Path(__file__).parents[3] / "ml" / "models"))

SEQ_LEN = 90


def _load_station_model(station_id: int):
    path = MODELS_DIR / f"station_{station_id}.pt"
    if not path.exists():
        return None, None
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    from app.services._lstm import LSTMAutoencoder
    model = LSTMAutoencoder()
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, checkpoint["threshold"]


def _score_windows(model, sequences: np.ndarray) -> np.ndarray:
    x = torch.tensor(sequences, dtype=torch.float32)
    with torch.no_grad():
        x_hat = model(x)
    errors = ((x_hat - x) ** 2).mean(dim=(1, 2)).numpy()
    return errors


async def get_anomalies(postcode: str, db: AsyncSession):
    lon, lat = get_coordinates(postcode)
    if lon is None:
        raise ValueError("Postcode not found")

    station = await get_nearest_station(lat, lon, db)
    if station is None:
        raise ValueError("No station found")

    model, threshold = _load_station_model(station.src_id)
    if model is None:
        raise ValueError(f"No model for station {station.src_id}")

    rows = await db.execute(text("""
        SELECT date, max_air_temp, min_air_temp, prcp_amt
        FROM observations
        WHERE station_id = :sid
          AND max_air_temp IS NOT NULL
          AND date >= NOW() - INTERVAL '10 years'
        ORDER BY date
    """), {"sid": station.src_id})
    rows = rows.fetchall()

    if len(rows) < SEQ_LEN:
        return []

    # Compute station stats for normalisation
    stats = await db.execute(text("""
        SELECT AVG(max_air_temp), STDDEV(max_air_temp),
               AVG(min_air_temp), STDDEV(min_air_temp),
               AVG(prcp_amt),     STDDEV(prcp_amt)
        FROM observations
        WHERE station_id = :sid AND max_air_temp IS NOT NULL
    """), {"sid": station.src_id})
    s = stats.fetchone()
    mean_max, std_max = s[0], s[1] or 1.0
    mean_min, std_min = s[2] or 0.0, s[3] or 1.0
    mean_rain, std_rain = s[4] or 0.0, s[5] or 1.0

    dates = [r[0] for r in rows]
    values = np.array([
        [
            ((r[1] or mean_max) - mean_max) / std_max,
            ((r[2] or mean_min) - mean_min) / std_min,
            ((r[3] or mean_rain) - mean_rain) / std_rain,
        ]
        for r in rows
    ], dtype=np.float32)

    # Slide 90-day windows (non-overlapping for clean date ranges)
    windows, window_starts = [], []
    for i in range(0, len(values) - SEQ_LEN + 1, SEQ_LEN):
        windows.append(values[i:i + SEQ_LEN])
        window_starts.append(dates[i])

    if not windows:
        return []

    errors = _score_windows(model, np.array(windows))

    anomalies = []
    for i, (error, start) in enumerate(zip(errors, window_starts)):
        if error > threshold:
            end = dates[min(i * SEQ_LEN + SEQ_LEN - 1, len(dates) - 1)]
            anomalies.append({
                "start_date": start.date() if hasattr(start, "date") else start,
                "end_date": end.date() if hasattr(end, "date") else end,
                "severity": round(float(error) / threshold, 2),
            })

    anomalies.sort(key=lambda a: a["severity"], reverse=True)
    return anomalies
