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
    result = await session.execute(text("""
        SELECT src_id, name
        FROM stations s
        WHERE (
            SELECT COUNT(*) FILTER (WHERE max_air_temp IS NOT NULL)::float
            / NULLIF(COUNT(*), 0)
            FROM observations o
            WHERE o.station_id = s.src_id
        ) >= 0.8
        ORDER BY 6371000 * 2 * asin(sqrt(
            sin(radians((s.latitude - :lat) / 2))^2 +
            cos(radians(:lat)) * cos(radians(s.latitude)) *
            sin(radians((s.longitude - :lon) / 2))^2
        ))
        LIMIT 1
    """), {"lat": lat, "lon": lon})
    station = result.fetchone()

    if station is None:
        fallback = await session.execute(text("""
            SELECT src_id, name
            FROM stations
            ORDER BY 6371000 * 2 * asin(sqrt(
                sin(radians((latitude - :lat) / 2))^2 +
                cos(radians(:lat)) * cos(radians(latitude)) *
                sin(radians((longitude - :lon) / 2))^2
            ))
            LIMIT 1
        """), {"lat": lat, "lon": lon})
        station = fallback.fetchone()

    return station
    
    

