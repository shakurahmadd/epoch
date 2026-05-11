from fastapi import FastAPI, Depends, HTTPException
from app.services.location import get_coordinates, get_nearest_station, get_region
from dotenv import load_dotenv
import os
import math
from sqlalchemy import text
from app.models.climate_metrics import Climate_metric
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.narrative import router as narrative_router
from app.services.forecast import get_forecast as forecast_service
from app.services.anomaly import get_anomalies as anomaly_service


def clean_row(row: dict) -> dict:
    """Replace NaN/Inf float values with None so they serialise as JSON null."""
    return {
        k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
        for k, v in row.items()
    }


app = FastAPI()

app.include_router(narrative_router)

@app.get("/health")
def health_check():
    return {"status" : "ok"}


@app.get("/climate/history/{location}")
async def get_climate_history(location : str, db: AsyncSession = Depends(get_db)):
    lon, lat = get_coordinates(location)
    if (lon is None) or (lat is None):
        raise HTTPException(status_code=400, detail="Postcode does not exist")
    station = await get_nearest_station(lat, lon, db)
    climate_metrics = await db.execute(text("""SELECT * FROM climate_metrics WHERE station_id = :src_id"""), {"src_id": station.src_id})
    climate_metric_rows = climate_metrics.fetchall()
    return [dict(row._mapping) for row in climate_metric_rows]


@app.get("/climate/timeline/{location}/{birth_year}")
async def get_birth_year_timeline(location : str, birth_year: int, db : AsyncSession = Depends(get_db)):
    lon, lat = get_coordinates(location)
    if (lon is None) or (lat is None):
        raise HTTPException(status_code=400, detail="Postcode does not exist")
    station = await get_nearest_station(lat, lon, db)
    region = get_region(location)
    climate_timeline = await db.execute(text("""SELECT * FROM climate_metrics WHERE station_id = :src_id AND year >= :birth_year ORDER BY year"""),
                                             {"src_id" : station.src_id, "birth_year" : birth_year})
    rows = climate_timeline.fetchall()
    metrics = [clean_row(dict(row._mapping)) for row in rows]
    total_years = len(metrics)

    # Simple linear trend: difference between last and first avg_max_temp per decade
    temps = [m['avg_max_temp'] for m in metrics if m['avg_max_temp'] is not None]
    trend_temp = None
    if len(temps) >= 2:
        trend_temp = round((temps[-1] - temps[0]) / (total_years / 10), 2)

    return {
        "location": location.upper(),
        "birth_year": birth_year,
        "station_name": station.name,
        "region": region,
        "metrics": metrics,
        "trend_temp": trend_temp,
        "total_years": total_years,
    }


@app.get("/climate/forecast/{postcode}")
async def get_climate_forecast(postcode: str, db: AsyncSession = Depends(get_db)):
    try:
        return await forecast_service(postcode, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/climate/anomalies/{postcode}")
async def get_climate_anomalies(postcode: str, db: AsyncSession = Depends(get_db)):
    try:
        return await anomaly_service(postcode, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

 
 