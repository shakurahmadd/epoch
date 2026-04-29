from app.db.base import Base
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime

class Climate_metric(Base):
    __tablename__ = "climate_metrics"

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.src_id"))
    avg_max_temp = Column(Float, nullable=True)
    avg_min_temp = Column(Float, nullable=True)
    avg_prcp = Column(Float, nullable=True)
    hot_days = Column(Integer, nullable=True)
    frost_days = Column(Integer, nullable=True)
    heavy_rain_days = Column(Integer, nullable=True)
    year = Column(Integer, nullable=False)




