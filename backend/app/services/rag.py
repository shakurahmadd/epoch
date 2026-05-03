from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

async def get_relevant_events(db: AsyncSession, region: str, birth_year:int, k: int=3):
    if "England" in region:
        country = "England"
    elif "Scotland" in region:
        country = "Scotland"
    elif "Wales" in region:
        country = "Wales"
    else:
        country = region

    query = f"Climate events in {region} since {birth_year}"
    query_embedding = model.encode(query)
    query_embedding = query_embedding.tolist()

    result = await db.execute(text("""SELECT * 
                                   FROM climate_events 
                                   WHERE year > :year 
                                   AND region IN (:region, :country, 'UK')
                                   ORDER BY embedding <=> :query_embedding LIMIT :k"""), 
                                   {"year" : birth_year, 'region' : region, "query_embedding" : query_embedding, 'k' : k, 'country' : country})
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]