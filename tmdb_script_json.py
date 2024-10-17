import os
import requests
import gzip
import shutil
import pandas as pd
import json
import sqlalchemy
from datetime import datetime, timedelta
import schedule
import time
import psycopg2
from psycopg2 import Error
from sqlalchemy import create_engine,text

database_uri = 'postgresql+psycopg2://postgres:Rootsqlipssi@localhost:5432/tmdb_movies'
 
try:
    engine = create_engine(database_uri)
   
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
database_uri = 'postgresql+psycopg2://postgres:Rootsqlipssi@localhost:5432/tmdb_movies'
 

date = (datetime.now() - timedelta(days=1)).strftime("%m_%d_%Y")
url = f"https://files.tmdb.org/p/exports/movie_ids_{date}.json.gz"
download_path = f"movie_ids_{date}.json.gz"
output_json_path = f"movie_ids_{date}.json"

def download_and_decompress(url, download_path, output_json_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(download_path, 'wb') as f:
            f.write(response.content)
        with gzip.open(download_path, 'rb') as f_in:
            with open(output_json_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print("Fichier téléchargé et décompressé avec succès.")
    else:
        print("Erreur lors du téléchargement du fichier.")

def load_json_to_dataframe(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        json_list = [json.loads(line) for line in f]
    df = pd.DataFrame(json_list)
    return df

def insert_dataframe_to_db(df, table_name, database_uri):
    engine = sqlalchemy.create_engine(database_uri)
    with engine.connect() as connection:
        df.to_sql(table_name, con=connection, if_exists='replace', index=False)
    print(f"Données insérées dans la table {table_name} avec succès.")

if __name__ == "__main__":
    download_and_decompress(url, download_path, output_json_path)

    df = load_json_to_dataframe(output_json_path)

    insert_dataframe_to_db(df, 'tmdb_movies', database_uri)

    os.remove(download_path)
    os.remove(output_json_path)
    print("Fichiers temporaires supprimés.")

def schedule_update():

    schedule.every(90).days.do(lambda: download_and_decompress(url, download_path, output_json_path))
    schedule.every(90).days.do(lambda: insert_dataframe_to_db(load_json_to_dataframe(output_json_path), 'tmdb_movies', database_uri))
    
    while True:
        schedule.run_pending()
        time.sleep(1)

#schedule_update()
