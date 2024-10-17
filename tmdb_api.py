import streamlit as st
import requests
import aiohttp
import time
import os
from dotenv import load_dotenv
import asyncio
import sys
from aiocache import cached
from aiocache.serializers import JsonSerializer

# Charger la variable d'environnement
load_dotenv()
api_key = os.getenv('API_KEY')

# Fonction pour obtenir les informations sur le film
def get_movie_info(movie_id):
    base_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
    response = requests.get(base_url)
    if response.status_code == 200:
        movie_info = response.json()
        title = movie_info.get('title')
        release_date = movie_info.get('release_date')
        genres = [genre['name'] for genre in movie_info.get('genres', [])]
        vote_average = movie_info.get('vote_average')
        popularity = movie_info.get('popularity')
        return title, release_date, genres, vote_average, popularity
    else:
        return f"Erreur : le film avec l'ID {movie_id} n'a pas été trouvé."

# Fonction robuste pour obtenir les informations sur le film
def get_movie_info_robuste(movie_id, retries=3, delay=2):
    base_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
    
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(base_url, timeout=10) 
            if response.status_code == 200:
                movie_info = response.json()
                title = movie_info.get('title')
                release_date = movie_info.get('release_date')
                genres = [genre['name'] for genre in movie_info.get('genres', [])]
                vote_average = movie_info.get('vote_average')
                popularity = movie_info.get('popularity')
                return title, release_date, genres, vote_average, popularity
            elif response.status_code == 404:
                return f"Erreur : le film avec l'ID {movie_id} n'a pas été trouvé."
            else:
                st.warning(f"Tentative {attempt} : Erreur avec le code {response.status_code}")
        
        except requests.exceptions.Timeout:
            st.warning(f"Tentative {attempt} : Timeout. Nouvelle tentative après {delay} secondes...")
        
        except requests.exceptions.ConnectionError:
            st.warning(f"Tentative {attempt} : Problème de connexion. Nouvelle tentative après {delay} secondes...")
        
        except Exception as e:
            st.error(f"Tentative {attempt} : Une erreur inattendue s'est produite : {str(e)}")
        
        time.sleep(delay)

    return f"Erreur : Impossible de récupérer les informations du film après {retries} tentatives."

# Fonction asynchrone pour obtenir les informations sur le film
semaphore = asyncio.Semaphore(50)
async def get_movie_info_async(movie_id):
    base_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
    
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                if response.status == 200:
                    movie_info = await response.json()
                    title = movie_info.get('title')
                    release_date = movie_info.get('release_date')
                    genres = [genre['name'] for genre in movie_info.get('genres', [])]
                    vote_average = movie_info.get('vote_average')
                    popularity = movie_info.get('popularity')
                    return title, release_date, genres, vote_average, popularity
                else:
                    st.warning(f"Erreur avec le code {response.status} pour le film {movie_id}")
                    return None

# Fonction asynchrone pour obtenir les informations sur le film avec mise en cache
@cached(ttl=3600, serializer=JsonSerializer())
async def get_movie_info_async_cached(movie_id):
    base_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
    
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                if response.status == 200:
                    movie_info = await response.json()
                    title = movie_info.get('title')
                    release_date = movie_info.get('release_date')
                    genres = [genre['name'] for genre in movie_info.get('genres', [])]
                    vote_average = movie_info.get('vote_average')
                    popularity = movie_info.get('popularity')
                    return title, release_date, genres, vote_average, popularity
                else:
                    st.warning(f"Erreur avec le code {response.status} pour le film {movie_id}")
                    return None

# Interface Streamlit
st.title("Informations sur le film - API Tests")

# Création des pages pour séparer les API
pages = ["API Simple", "API Robuste", "API Asynchrone", "API Asynchrone avec Cache"]
page = st.sidebar.selectbox("Sélectionnez une API", pages)

if page == "API Simple":
    st.header("API Simple")
    movie_id = st.text_input("Entrez l'ID du film (API Simple) :", "550", key="simple")
    if st.button("Obtenir les informations (simple)", key="button_simple"):
        movie_info = get_movie_info(movie_id)
        if isinstance(movie_info, tuple):
            title, release_date, genres, vote_average, popularity = movie_info
            st.write(f"**Titre :** {title}")
            st.write(f"**Date de sortie :** {release_date}")
            st.write(f"**Genres :** {', '.join(genres)}")
            st.write(f"**Note moyenne :** {vote_average}")
            st.write(f"**Popularité :** {popularity}")
        else:
            st.error(movie_info)

elif page == "API Robuste":
    st.header("API Robuste")
    movie_id = st.text_input("Entrez l'ID du film (API Robuste) :", "550", key="robuste")
    if st.button("Obtenir les informations (robuste)", key="button_robuste"):
        movie_info = get_movie_info_robuste(movie_id)
        if isinstance(movie_info, tuple):
            title, release_date, genres, vote_average, popularity = movie_info
            st.write(f"**Titre :** {title}")
            st.write(f"**Date de sortie :** {release_date}")
            st.write(f"**Genres :** {', '.join(genres)}")
            st.write(f"**Note moyenne :** {vote_average}")
            st.write(f"**Popularité :** {popularity}")
        else:
            st.error(movie_info)

elif page == "API Asynchrone":
    st.header("API Asynchrone")
    movie_id_start = st.text_input("Entrez l'ID de début du film (API Asynchrone) :", "550", key="async_start")
    movie_id_end = st.text_input("Entrez l'ID de fin du film (API Asynchrone) :", "555", key="async_end")
    if st.button("Obtenir les informations (asynchrone)", key="button_async"):
        async def run_async():
            tasks = []
            for movie_id in range(int(movie_id_start), int(movie_id_end) + 1):
                tasks.append(get_movie_info_async(movie_id))
            results = await asyncio.gather(*tasks)
            for movie_info in results:
                if movie_info:
                    title, release_date, genres, vote_average, popularity = movie_info
                    st.write(f"**Titre :** {title}")
                    st.write(f"**Date de sortie :** {release_date}")
                    st.write(f"**Genres :** {', '.join(genres)}")
                    st.write(f"**Note moyenne :** {vote_average}")
                    st.write(f"**Popularité :** {popularity}")
        asyncio.run(run_async())

elif page == "API Asynchrone avec Cache":
    st.header("API Asynchrone avec Cache")
    movie_id_start = st.text_input("Entrez l'ID de début du film (API Asynchrone avec Cache) :", "550", key="async_cached_start")
    movie_id_end = st.text_input("Entrez l'ID de fin du film (API Asynchrone avec Cache) :", "555", key="async_cached_end")
    if st.button("Obtenir les informations (asynchrone avec cache)", key="button_async_cached"):
        async def run_async_cached():
            tasks = []
            for movie_id in range(int(movie_id_start), int(movie_id_end) + 1):
                tasks.append(get_movie_info_async_cached(movie_id))
            results = await asyncio.gather(*tasks)
            for movie_info in results:
                if movie_info:
                    title, release_date, genres, vote_average, popularity = movie_info
                    st.write(f"**Titre :** {title}")
                    st.write(f"**Date de sortie :** {release_date}")
                    st.write(f"**Genres :** {', '.join(genres)}")
                    st.write(f"**Note moyenne :** {vote_average}")
                    st.write(f"**Popularité :** {popularity}")
        asyncio.run(run_async_cached())
