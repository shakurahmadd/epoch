from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DB_URL)

session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with session_factory() as session:
        yield session