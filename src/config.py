"""
config.py
---------
Ce fichier lit le fichier .env et rend les paramètres disponibles
pour tous les autres scripts du projet.

Utilisation dans un autre fichier :
    from src.config import OPEN_METEO_URL, BRONZE_DIR, ...
"""

import os
from dotenv import load_dotenv

# Charge le fichier .env
load_dotenv()

# URL de l'API Open-Meteo
OPEN_METEO_URL = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")

# Dossier où sauvegarder les fichiers JSON bruts
BRONZE_DIR = os.getenv("BRONZE_DIR", "data/bronze")

# Chemin du fichier CSV des villes
CITIES_CSV = os.getenv("CITIES_CSV", "ma.csv")

# Population minimale pour inclure une ville
MIN_POPULATION = int(os.getenv("MIN_POPULATION", 100000))

# Nombre de jours de prévision
FORECAST_DAYS = int(os.getenv("FORECAST_DAYS", 7))

# Timeout réseau en secondes
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 10))

# Nombre de tentatives en cas d'échec
API_RETRIES = int(os.getenv("API_RETRIES", 3))

# Variables météo qu'on demande à l'API
# Ces noms sont imposés par Open-Meteo (voir leur documentation)
DAILY_VARIABLES = [
    "temperature_2m_max",    # température maximale du jour (°C)
    "temperature_2m_min",    # température minimale du jour (°C)
    "precipitation_sum",     # total des précipitations (mm)
    "windspeed_10m_max",     # vitesse max du vent (km/h)
    "windgusts_10m_max",     # rafales max du vent (km/h)
    "weathercode",           # code météo WMO (0=clair, 95=orage, etc.)
    "precipitation_hours",   # nombre d'heures avec pluie
]
