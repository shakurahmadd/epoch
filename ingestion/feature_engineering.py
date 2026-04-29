from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))
from app.models.climate_metrics import Climate_metric
from app.models.station import Station

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")


query = """SELECT station_id, EXTRACT(YEAR FROM date) as year, 
AVG(max_air_temp) as avg_max_temp, AVG(min_air_temp) as avg_min_temp, AVG(prcp_amt) as avg_prcp, COUNT(CASE WHEN max_air_temp >= 25 THEN 1 END) as hot_days,
 COUNT(CASE WHEN min_air_temp <=0 THEN 1 END) as frost_days, 
 COUNT(CASE WHEN prcp_amt >=10 THEN 1 END) as heavy_rain_days
 FROM observations GROUP BY station_id,
 EXTRACT(YEAR FROM date)""" 


engine = create_engine(DB_URL.replace("asyncpg", "psycopg2"))
session_factory = sessionmaker(engine, expire_on_commit=False)

session = session_factory()
query_rows = session.execute(text(query))

for row in query_rows:
    climate_metric_row = Climate_metric (station_id = row.station_id, avg_max_temp = row.avg_max_temp, avg_min_temp=row.avg_min_temp, 
                   avg_prcp = row.avg_prcp, hot_days = row.hot_days, frost_days = row.frost_days, 
                   heavy_rain_days = row.heavy_rain_days, year=row.year)
    session.merge(climate_metric_row)

session.commit()



