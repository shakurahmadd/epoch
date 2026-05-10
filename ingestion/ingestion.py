from dotenv import load_dotenv
import os
import requests
import pandas as pd
from io import StringIO
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))
from app.models.observations import Observation
from app.models.station import Station


load_dotenv()

CEDA_TOKEN = os.getenv("CEDA_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

def get_file_url(county, src_id, station_file_name, year, dataset):
    base_url = f'https://dap.ceda.ac.uk/badc/ukmo-midas-open/data/{dataset}/dataset-version-202507/{county}/'
    directory_path = f'{src_id}_{station_file_name}/qc-version-1/'
    filename = f"midas-open_{dataset}_dv-202507_{county}_{src_id}_{station_file_name}_qcv-1_{year}.csv"

    return base_url + directory_path + filename


def download_file(url):
    headers = {"Authorization" : f"Bearer {CEDA_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        print(f"error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"error: {e}")
        return None
    

def parse_observations(response):
    observation_lines = response.text.split('\n')
    start_row = None
    for idx, line in enumerate(observation_lines):
        if line.strip() == 'data':
            start_row = idx
    observations_df = pd.read_csv(StringIO(response.text), skiprows=start_row + 1)
    observations_df = observations_df[observations_df['ob_end_time'] != 'end data']
    observation_cols = ['src_id', 'ob_end_time', 'max_air_temp', 'min_air_temp']
    observations_df = observations_df[observation_cols]
    observations_df_filtered = observations_df.groupby([pd.to_datetime(observations_df['ob_end_time']).dt.date,
                                                         'src_id']).agg({'max_air_temp':'max', 'min_air_temp' : 'min'}).reset_index()
    return observations_df_filtered


def parse_rainfall(response):
    observation_rain_lines = response.text.split('\n')
    start_row = None
    for idx, line in enumerate(observation_rain_lines):
        if line.strip() == 'data':
            start_row = idx
    observations_rain_df = pd.read_csv(StringIO(response.text), skiprows=start_row + 1)
    observations_rain_df = observations_rain_df[observations_rain_df['ob_date'] != 'end data']
    rain_cols = ['src_id', 'ob_date', 'prcp_amt']
    observations_rain_df = observations_rain_df[rain_cols]
    return observations_rain_df


def insert_observations(df, session):
    from sqlalchemy import text
    for index, row in df.iterrows():
        if 'ob_end_time' in row.index:
            session.execute(text("""
                INSERT INTO observations (station_id, date, max_air_temp, min_air_temp, prcp_amt)
                VALUES (:sid, :date, :max_t, :min_t, NULL)
                ON CONFLICT (station_id, date) DO UPDATE SET
                    max_air_temp = COALESCE(observations.max_air_temp, EXCLUDED.max_air_temp),
                    min_air_temp = COALESCE(observations.min_air_temp, EXCLUDED.min_air_temp)
            """), {"sid": row['src_id'], "date": row['ob_end_time'],
                   "max_t": row['max_air_temp'], "min_t": row['min_air_temp']})
        else:
            session.execute(text("""
                INSERT INTO observations (station_id, date, max_air_temp, min_air_temp, prcp_amt)
                VALUES (:sid, :date, NULL, NULL, :prcp)
                ON CONFLICT (station_id, date) DO UPDATE SET
                    prcp_amt = COALESCE(observations.prcp_amt, EXCLUDED.prcp_amt)
            """), {"sid": row['src_id'], "date": row['ob_date'], "prcp": row['prcp_amt']})
    session.commit()
    return "Observation rows have been added"

        
def insert_stations(df, session):
    for index, row in df.iterrows():
        db_station_row = Station(src_id= row['src_id'], name = row['station_name'], longitude=row['station_longitude'],
                                  latitude=row['station_latitude'], elevation = row['station_elevation'],
                                    first_year=row['first_year'], last_year=row['last_year'])
        session.merge(db_station_row)
    session.commit()



engine = create_engine(DB_URL.replace("asyncpg", "psycopg2"))
session_factory = sessionmaker(engine, expire_on_commit=False)



def main():
    with open("midas-open_uk-daily-temperature-obs_dv-202507_station-metadata.csv", "r") as f:
        meta_data = f.readlines()
    first_row = None
    for idx, line in enumerate(meta_data):
        if line.strip() == 'data':
            first_row = idx
    meta_data_df = pd.read_csv("midas-open_uk-daily-temperature-obs_dv-202507_station-metadata.csv", skiprows=first_row + 1)
    meta_data_df = meta_data_df[meta_data_df['src_id'] != 'end data']
    meta_data_df = meta_data_df[(meta_data_df['last_year'] >= 2024) & (meta_data_df['first_year'] >= 1960)]
    session = session_factory()

    with open("midas-open_uk-daily-rain-obs_dv-202507_station-metadata.csv", "r") as f:
        rain_meta_data = f.readlines()
    start_row = None
    for idx, line in enumerate(rain_meta_data):
        if line.strip() == 'data':
            start_row = idx
    rain_meta_df = pd.read_csv("midas-open_uk-daily-rain-obs_dv-202507_station-metadata.csv", skiprows=start_row+1)
    rain_meta_df = rain_meta_df[rain_meta_df['src_id'] != 'end data']
    rain_meta_df = rain_meta_df[rain_meta_df['src_id'].isin(meta_data_df['src_id'])]
    insert_stations(meta_data_df, session)

    for index, row in meta_data_df.iterrows():
        for year in range(int(row['first_year']), int(row['last_year']) + 1):
            temp_file_url = get_file_url(row['historic_county'], row['src_id'], row['station_file_name'], year, "uk-daily-temperature-obs")
            response = download_file(temp_file_url)
            if response is None:
                continue
            else:
                temp_obvs_df = parse_observations(response)
                insert_observations(temp_obvs_df, session)
        print(f"Completed {row['station_name']} temp observation {index} out of {len(meta_data_df)}")

    for index, row in rain_meta_df.iterrows():
        for year in range(int(row['first_year']), int(row['last_year']) + 1):
            rain_file_url = get_file_url(row['historic_county'], row['src_id'], row['station_file_name'], year, "uk-daily-rain-obs")
            response = download_file(rain_file_url)
            if response is None:
                continue
            else:
                rain_obvs_df = parse_rainfall(response)
                insert_observations(rain_obvs_df, session)
        print(f"Completed {row['station_name']} rain observation {index} out of {len(meta_data_df)}")


if __name__ == "__main__": main()