from app.db.base import Base
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime

class Observation(Base):
    __tablename__ = 'observations'

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.src_id"))
    date = Column(DateTime, nullable=False)
    max_air_temp = Column(Float, nullable=True)
    min_air_temp = Column(Float, nullable=True)
    prcp_amt = Column(Float, nullable=True)