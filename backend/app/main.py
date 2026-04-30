from fastapi import FastAPI, Depends
from app.services.location import get_coordinates, get_nearest_station
from dotenv import load_dotenv
import os
from sqlalchemy import text
from app.models.climate_metrics import Climate_metric
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


app = FastAPI()

@app.get("/health")
def health_check():
    return {"status" : "ok"}


@app.get("/climate/history/{location}")
async def get_climate_history(location : str, db: AsyncSession = Depends(get_db)):
    lon, lat = get_coordinates(location)
    station = await get_nearest_station(lat, lon, db)
    climate_metrics = await db.execute(text("""SELECT * FROM climate_metrics WHERE station_id = :src_id"""), {"src_id": station.src_id})
    climate_metric_rows = climate_metrics.fetchall()
    return [dict(row._mapping) for row in climate_metric_rows]


@app.get("/climate/timeline/{location}/{birth_year}")
async def get_birth_year_timeline(location : str, birth_year: int, db : AsyncSession = Depends(get_db)):
    lon, lat = get_coordinates(location)
    station = await get_nearest_station(lat, lon, db)
    climate_timeline = await db.execute(text("""SELECT * FROM climate_metrics WHERE station_id = :src_id AND year >= :birth_year"""), 
                                             {"src_id" : station.src_id, "birth_year" : birth_year})
    climate_timeline = climate_timeline.fetchall()
    return [dict(row._mapping) for row in climate_timeline]
    
 
