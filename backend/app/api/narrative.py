from pydantic import BaseModel
from app.db.database import get_db
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.location import get_coordinates, get_nearest_station
from sqlalchemy import text
from app.services.rag import generate_narrative, get_relevant_events


class NarrativeRequest(BaseModel):
    birth_year : int
    region : str
    postcode : str

router = APIRouter()

@router.post("/narrative")
async def get_narrative(narrative_request : NarrativeRequest, db: AsyncSession = Depends(get_db)):
    lon, lat = get_coordinates(narrative_request.postcode)
    station = await get_nearest_station(lat, lon, db)
    climate_metrics = await db.execute(text("SELECT avg_max_temp, avg_min_temp, avg_prcp, hot_days, frost_days, heavy_rain_days, year FROM climate_metrics WHERE station_id =:station_id AND year >=:year"), 
                                       {"station_id" : station.src_id, "year" : narrative_request.birth_year})
    climate_metrics = climate_metrics.fetchall()
    climate_metrics = "\n".join([f"{row.year}: avg_max={row.avg_max_temp}, avg_min={row.avg_min_temp}, prcp={row.avg_prcp}, hot_days={row.hot_days}, frost_days={row.frost_days}, heavy_rain={row.heavy_rain_days}" for row in climate_metrics])
    events = await get_relevant_events(db, narrative_request.region, narrative_request.birth_year)
    response = await generate_narrative(climate_metrics, events, narrative_request.region, narrative_request.birth_year)
    return response 


