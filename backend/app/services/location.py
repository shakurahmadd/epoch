import requests
from sqlalchemy import text


def get_coordinates(postcode):
    try:
        coordinates_response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
        coordinates_response.raise_for_status()
        lon = coordinates_response.json()['result']['longitude']
        lat = coordinates_response.json()['result']['latitude']
        return lon, lat

    except requests.exceptions.HTTPError as e:
        print(e)
        return None
    



async def get_nearest_station(lat, lon, session):
    closest_stations = await session.execute(text("""SELECT src_id, name FROM stations ORDER BY ((latitude - :lat)^2 + (longitude - :lon)^2) LIMIT 1"""), 
                                      {"lat": lat, "lon": lon})
    closest_station = closest_stations.fetchone()
    return closest_station
    
    

