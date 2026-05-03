from app.db.base import Base
from sqlalchemy import String, Integer, Float, Text, Column
from pgvector.sqlalchemy import Vector


class ClimateEvents(Base):
    __tablename__ = "climate_events"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    embedding = Column(Vector(384), nullable=False)
