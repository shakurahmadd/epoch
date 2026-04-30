from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL.replace("asyncpg", "psycopg2"))
session_factory = sessionmaker(engine, expire_on_commit=False)
session = session_factory()

query = """
SELECT station_id, year, avg_max_temp, hot_days, frost_days, latitude, longitude, elevation
FROM climate_metrics
INNER JOIN stations ON climate_metrics.station_id = stations.src_id
WHERE station_id IN (SELECT station_id FROM climate_metrics GROUP BY station_id HAVING COUNT(*) >=30 )
"""

rows = session.execute(text(query))
rows = rows.fetchall()

exported_data = [dict(row._mapping) for row in rows]
exported_data = pd.DataFrame(exported_data)
exported_data.to_csv('climate_training_data.csv', index=False)