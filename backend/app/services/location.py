import requests
from sqlalchemy import text


def get_coordinates(postcode):
    try:
        coordinates_response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
        coordinates_response.raise_for_status()
        result = coordinates_response.json()['result']
        lon = result['longitude']
        lat = result['latitude']
        return lon, lat

    except requests.exceptions.HTTPError as e:
        print(e)
        return None, None


def get_region(postcode):
    try:
        coordinates_response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
        coordinates_response.raise_for_status()
        result = coordinates_response.json()['result']
        return result.get('region') or result.get('country') or 'UK'
    except requests.exceptions.HTTPError:
        return 'UK'
    



async def get_nearest_station(lat, lon, session):
    closest_stations = await session.execute(text("""SELECT src_id, name FROM stations ORDER BY ((latitude - :lat)^2 + (longitude - :lon)^2) LIMIT 1"""), 
                                      {"lat": lat, "lon": lon})
    closest_station = closest_stations.fetchone()
    return closest_station
    
    

