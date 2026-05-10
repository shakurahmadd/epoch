from app.db.base import Base
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, PrimaryKeyConstraint

class Observation(Base):
    __tablename__ = 'observations'

    station_id = Column(Integer, ForeignKey("stations.src_id"), nullable=False)
    date = Column(DateTime, nullable=False)
    max_air_temp = Column(Float, nullable=True)
    min_air_temp = Column(Float, nullable=True)
    prcp_amt = Column(Float, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('station_id', 'date'),
    )