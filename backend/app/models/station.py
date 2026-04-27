from app.db.base import Base
from sqlalchemy import String, Integer, Float, DateTime, Column

class Station(Base):
    __tablename__ = 'stations'

    src_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=False)
    first_year = Column(Integer, nullable=False)
    last_year = Column(Integer, nullable=True)
    
