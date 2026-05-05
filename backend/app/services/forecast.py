import torch
import torch.nn as nn
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from huggingface_hub import hf_hub_download
from app.services.location import get_coordinates, get_nearest_station


class TFT(nn.Module):
    def __init__(self):
        super().__init__()
        # LSTM takes 6 features per time step, produces 64-dim hidden state
        self.lstm = nn.LSTM(input_size=6, hidden_size=64, batch_first=True)
        # Linear maps the final hidden state to 14 steps * 3 quantiles = 42 values
        self.linear = nn.Linear(64, 42)

    def forward(self, x):
        output, (hidden, cell) = self.lstm(x)
        # Take only the last time step's output
        final_output = output[:, -1, :]
        result = self.linear(final_output)
        # Reshape to [batch, 14 prediction steps, 3 quantiles]
        result = result.view(-1, 14, 3)
        return result


# Load model once at module level — avoids re-downloading on every request
_model = None

def _get_model():
    global _model
    if _model is None:
        # Download weights from HuggingFace Hub
        weights_path = hf_hub_download(
            repo_id="shakurahmad/epoch-tft-mvp",
            filename="epoch_mvp_weights.pt"
        )
        _model = TFT()
        # map_location="cpu" ensures it works on servers without a GPU
        _model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        _model.eval()
    return _model


async def get_forecast(postcode: str, db: AsyncSession) -> dict:
    # Step 1: postcode → coordinates → nearest station
    lon, lat = get_coordinates(postcode)
    if lon is None:
        raise ValueError(f"Invalid postcode: {postcode}")

    station = await get_nearest_station(lat, lon, db)
    station_id = station.src_id
    station_name = station.name

    # Step 2: fetch all historical metrics for this station, ordered by year
    result = await db.execute(
        text("""
            SELECT cm.year, cm.avg_max_temp, cm.hot_days, cm.frost_days,
                   s.latitude, s.longitude, s.elevation
            FROM climate_metrics cm
            JOIN stations s ON cm.station_id = s.src_id
            WHERE cm.station_id = :sid
            ORDER BY cm.year
        """),
        {"sid": station_id}
    )
    rows = result.fetchall()

    if len(rows) < 15:
        raise ValueError(f"Not enough historical data for station {station_id} (need 15 years, have {len(rows)})")

    # Step 3: build numpy arrays from the last 15 rows
    # Feature order must match training: hot_days, frost_days, latitude, longitude, elevation, year
    window = rows[-15:]

    hot_days   = np.array([r.hot_days   for r in window], dtype=np.float32)
    frost_days = np.array([r.frost_days for r in window], dtype=np.float32)
    latitudes  = np.array([r.latitude   for r in window], dtype=np.float32)
    longitudes = np.array([r.longitude  for r in window], dtype=np.float32)
    elevations = np.array([r.elevation  for r in window], dtype=np.float32)
    years      = np.array([r.year       for r in window], dtype=np.float32)
    temps      = np.array([r.avg_max_temp for r in window], dtype=np.float32)

    # Step 4: z-score scale per-station (same as training)
    def z_score(arr):
        mu, sigma = arr.mean(), arr.std()
        # Avoid division by zero for constant columns
        return (arr - mu) / (sigma if sigma > 0 else 1.0), mu, sigma

    hot_days_s,   _,        _        = z_score(hot_days)
    frost_days_s, _,        _        = z_score(frost_days)
    years_s,      _,        _        = z_score(years)
    _,            temp_mu,  temp_std = z_score(temps)

    # Global features: scale using the window's own stats
    lat_s  = (latitudes  - latitudes.mean())  / (latitudes.std()  if latitudes.std()  > 0 else 1.0)
    lon_s  = (longitudes - longitudes.mean()) / (longitudes.std() if longitudes.std() > 0 else 1.0)
    elev_s = (elevations - elevations.mean()) / (elevations.std() if elevations.std() > 0 else 1.0)

    # Stack into [15, 6] — training column order
    features = np.stack([hot_days_s, frost_days_s, lat_s, lon_s, elev_s, years_s], axis=1)

    # Step 5: convert to tensor and add batch dimension → [1, 15, 6]
    input_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)

    # Step 6: run inference
    model = _get_model()
    with torch.no_grad():
        predictions = model(input_tensor)  # [1, 14, 3]

    # Step 7: unscale — reverse the z-score on avg_max_temp
    preds_np = predictions.squeeze(0).numpy()  # [14, 3]
    preds_unscaled = preds_np * temp_std + temp_mu

    # Step 8: build response — 14 years from the year after the last known data point
    last_year = int(rows[-1].year)
    forecast_years = list(range(last_year + 1, last_year + 15))

    forecast = [
        {
            "year": forecast_years[i],
            "q10": round(float(preds_unscaled[i, 0]), 3),
            "q50": round(float(preds_unscaled[i, 1]), 3),
            "q90": round(float(preds_unscaled[i, 2]), 3),
        }
        for i in range(14)
    ]

    return {
        "station_name": station_name,
        "forecast": forecast,
    }
