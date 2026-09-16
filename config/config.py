import os
from dotenv import load_dotenv

# Trouve le .env à la racine du projet, peu importe d'où on lance le script
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Fichier CSV des villes
CITIES_CSV = os.getenv("CITIES_CSV", "ma.csv")

# Population minimale pour filtrer les villes
MIN_POPULATION = int(os.getenv("MIN_POPULATION", 100000))

# API Open-Meteo (gratuite, sans clé)
OPEN_METEO_URL = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")

# Nombre de jours de prévision
FORECAST_DAYS = int(os.getenv("FORECAST_DAYS", 7))

# Timeout et tentatives pour les appels API
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 10))
API_RETRIES = int(os.getenv("API_RETRIES", 3))

# Chemins des dossiers de données
ROOT_DIR   = ROOT_DIR
BRONZE_DIR = os.path.join(ROOT_DIR, os.getenv("BRONZE_DIR", "data/bronze"))
SILVER_DIR = os.path.join(ROOT_DIR, os.getenv("SILVER_DIR", "data/silver"))
GOLD_DIR   = os.path.join(ROOT_DIR, os.getenv("GOLD_DIR",   "data/gold"))

# Variables météo demandées à l'API
DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "windspeed_10m_max",
    "windgusts_10m_max",
    "weathercode",
    "precipitation_hours",
]

# PostgreSQL
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "climaLog")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?ssl=false"
