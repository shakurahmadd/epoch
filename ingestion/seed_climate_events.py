from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))                                                     
from app.models.climate_events import ClimateEvents

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL.replace("asyncpg", "psycopg2"))
session_factory = sessionmaker(engine, expire_on_commit=False)
session = session_factory()

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

EVENTS = [
    {"title": "1976 UK Drought", "year": 1976, "region": "England", "summary": "The most severe drought in UK records. Sixteen months of below-average rainfall caused reservoir levels to collapse. Standpipes were erected in streets across Wales and southwest England. The government appointed a Minister for Drought."},
    {"title": "1987 Great Storm", "year": 1987, "region": "Southeast England", "summary": "Hurricane-force winds of up to 115mph struck southern England overnight on 15-16 October. Fifteen million trees were uprooted. Eighteen people died. The storm caused £2 billion in damage and was the worst since 1703."},
    {"title": "1990 Burns Day Storm", "year": 1990, "region": "UK", "summary": "A severe extratropical cyclone struck the UK on 25 January with winds exceeding 100mph. Forty-seven people were killed across the UK and Europe. It caused more insurance losses than the 1987 Great Storm."},
    {"title": "1995 Summer Heatwave", "year": 1995, "region": "England", "summary": "The hottest and driest summer in central England since 1659. August 1995 was the warmest August on record at the time. Reservoir levels dropped critically and hosepipe bans were introduced across England and Wales."},
    {"title": "2000 Autumn Floods", "year": 2000, "region": "England", "summary": "The wettest autumn in England and Wales since records began in 1766. Widespread flooding affected York, Shrewsbury, Lewes, and hundreds of other towns. Over 10,000 properties flooded. Estimated damage exceeded £1 billion."},
    {"title": "2003 European Heatwave", "year": 2003, "region": "England", "summary": "The hottest summer on record in the UK at the time. Temperatures reached 38.5°C at Faversham, Kent on 10 August — the first time 38°C had been exceeded in the UK. Over 2,000 excess deaths were recorded in England."},
    {"title": "2004 Boscastle Flash Flood", "year": 2004, "region": "Southwest England", "summary": "On 16 August, extreme rainfall caused flash flooding in the village of Boscastle, Cornwall. Over 75mm of rain fell in two hours. Floodwaters reached 3 metres. Over 100 vehicles and 50 buildings were damaged. No fatalities."},
    {"title": "2007 Summer Floods", "year": 2007, "region": "England", "summary": "June and July 2007 were the wettest since records began. Severe flooding hit Hull, Sheffield, Gloucester, and Tewkesbury. Thirteen people died. Over 48,000 homes and 7,300 businesses were flooded. Damage estimated at £3 billion."},
    {"title": "2009 Cumbria Floods", "year": 2009, "region": "Northwest England", "summary": "In November 2009, record rainfall in Cumbria caused catastrophic flooding. Cockermouth received 314mm of rain in 24 hours — a UK record at the time. The River Derwent burst its banks destroying Workington's Northside Bridge. One police officer died."},
    {"title": "2010 Big Freeze", "year": 2010, "region": "UK", "summary": "December 2010 was the coldest December in the UK since 1910. Temperatures dropped to -21°C in Scotland. Widespread disruption to transport across the country. Snow lay on the ground for weeks across northern England and Scotland."},
    {"title": "2012 Wettest Year", "year": 2012, "region": "England", "summary": "2012 was the second wettest year in England since records began in 1910. The Thames flooded in February and again in November. Summer flooding caused widespread disruption. Despite record rainfall, a drought had been declared in spring."},
    {"title": "2013 St Jude Storm", "year": 2013, "region": "Southeast England", "summary": "A powerful extratropical cyclone struck southern England on 28 October with gusts exceeding 99mph. Four people were killed. Over 650,000 homes lost power. It was the most powerful storm to hit the southeast since 1987."},
    {"title": "2014 Winter Storms", "year": 2014, "region": "Southwest England", "summary": "A succession of Atlantic storms battered the UK from December 2013 to February 2014. The Somerset Levels flooded for weeks. The Dawlish sea wall was destroyed, severing the main rail line to Cornwall. It was the stormiest period in 100 years."},
    {"title": "2015 Desmond Floods", "year": 2015, "region": "Northwest England", "summary": "Storm Desmond brought record rainfall to Cumbria in December 2015. Honister Pass recorded 341.4mm in 24 hours — a new UK record. Carlisle and Kendal flooded severely. Over 5,000 homes were flooded and 61,000 lost power."},
    {"title": "2018 Beast from the East", "year": 2018, "region": "UK", "summary": "A sudden stratospheric warming event pushed Arctic air across the UK in late February and early March 2018. Temperatures fell to -14°C in Scotland. Heavy snowfall paralysed transport. At least ten people died from cold-related causes."},
    {"title": "2018 Summer Drought", "year": 2018, "region": "England", "summary": "The summer of 2018 was the joint hottest on record for the UK. A prolonged drought turned fields across England brown. Wildfires broke out on moorlands in Lancashire and Yorkshire. The dry spell lasted from May to August."},
    {"title": "2019 July Heatwave", "year": 2019, "region": "UK", "summary": "On 25 July 2019, Cambridge Botanic Garden recorded 38.7°C — a new UK temperature record. The heatwave affected the whole country with temperatures exceeding 35°C across much of England. Rail tracks buckled and power cables failed."},
    {"title": "2020 Storm Ciara and Dennis", "year": 2020, "region": "UK", "summary": "Storms Ciara and Dennis struck in quick succession in February 2020. Dennis brought the highest wind gust ever recorded in Wales at 93mph. Extensive flooding hit the Wye Valley, South Wales, and Yorkshire. Over 4,000 properties flooded."},
    {"title": "2021 Storm Arwen", "year": 2021, "region": "Northern England and Scotland", "summary": "Storm Arwen brought gusts of 98mph to northeast England and Scotland in November 2021. Three people were killed. Over 100,000 homes lost power, with some remaining without electricity for nearly two weeks — the longest outage since the 1987 storm."},
    {"title": "2022 July Heatwave", "year": 2022, "region": "England", "summary": "On 19 July 2022, Coningsby in Lincolnshire recorded 40.3°C — the first time 40°C had ever been recorded in the UK. The Met Office issued its first ever red extreme heat warning. Wildfires broke out across London. Over 3,000 excess deaths were recorded."},
    {"title": "2022 Drought", "year": 2022, "region": "England", "summary": "Following the July heatwave, England experienced its driest summer since 1935. A national drought was declared in August 2022 — the first since 2012. Rivers reached record low levels and several water companies imposed hosepipe bans."},
    {"title": "2023 Storm Babet", "year": 2023, "region": "Scotland", "summary": "Storm Babet struck Scotland in October 2023 bringing extreme rainfall. Angus and Aberdeenshire were worst affected with Brechin suffering its worst flooding in living memory. Four people died in Scotland. The River South Esk burst its banks flooding hundreds of homes."},
    {"title": "1953 East Coast Flood", "year": 1953, "region": "Eastern England", "summary": "A catastrophic North Sea storm surge struck the east coast of England on 31 January 1953. Over 1,600km of coastline was flooded. 307 people died in England, 19 in Scotland. 32,000 people were evacuated. It remains the deadliest peacetime disaster in the UK in the 20th century."},
    {"title": "1963 Big Freeze", "year": 1963, "region": "UK", "summary": "The winter of 1962-63 was the coldest in the UK since 1740. Snow fell every day somewhere in the UK from 26 December to 5 March. The sea froze at Herne Bay. Football matches were postponed for months. It remains the benchmark severe winter in living memory."},
    {"title": "2024 Storm Darragh", "year": 2024, "region": "UK", "summary": "Storm Darragh struck the UK in December 2024 with gusts exceeding 100mph in Wales and southwest England. It was one of the most powerful storms to hit the UK in years, causing widespread transport disruption, power outages affecting hundreds of thousands of homes, and significant structural damage across Wales and Ireland."},
]



for event in EVENTS:
    event_check = session.execute(text("SELECT * FROM climate_events WHERE title=:event_title AND year=:year"),
                     {'event_title' : event['title'], 'year' : event['year']}).fetchone()
    if event_check is None:
        summary_embedding = model.encode(event['summary'])
        summary_embedding = summary_embedding.tolist()
        event_row = ClimateEvents(title = event['title'], summary=event['summary'], year=event['year'], 
                                  region=event['region'], embedding=summary_embedding)
        session.add(event_row)
session.commit()









