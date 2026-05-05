from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv()


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
    query_embedding = str(query_embedding)

    result = await db.execute(text("""SELECT title, summary, year, region
                                   FROM climate_events
                                   WHERE year > :year
                                   AND region IN (:region, :country, 'UK')
                                   ORDER BY embedding <=> CAST(:query_embedding AS vector) LIMIT :k"""),
                                   {"year" : birth_year, 'region' : region, "query_embedding" : query_embedding, 'k' : k, 'country' : country})
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]



GROQ_API_KEY = os.getenv("GROQ_KEY")
client = AsyncGroq(api_key=GROQ_API_KEY)

async def generate_narrative(climate_data, events, region, birth_year):
    system_prompt = """You are a climate journalist writing personalised climate summaries for UK residents.
    Write in an conversational and friendly tone for a general audience.
    Produce a single paragraph of 200 words.
    Use only the climate data and historical events provided — do not add facts not present in the context.
    Always personalise the response to the specific region and birth year given."""

    user_prompt = f"Write a climate summary for someone born in {birth_year} living in {region}.\n\nClimate data:\n{climate_data}\n\nRelevant historical events:\n{events}"
    chat_completion = await client.chat.completions.create(
        messages=[{
            "role" : "system",
            "content" : system_prompt
        },         
            {
            "role" : "user",
            "content": user_prompt,
        }],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content
    


