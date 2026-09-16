"""
load_data.py
------------
Etape 5 - Chargement dans PostgreSQL

Ce script :
  1. Lit data/gold/weather_risk.csv
  2. Cree les tables dans PostgreSQL si elles n'existent pas
  3. Charge les donnees avec upsert (pas de doublons si on relance)
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import DB_URL, GOLD_DIR


# ─────────────────────────────────────────────
# SQL : creation des tables
# ─────────────────────────────────────────────

SQL_CREATE_CITIES = """
CREATE TABLE IF NOT EXISTS cities (
    id         SERIAL PRIMARY KEY,
    city       VARCHAR(100) UNIQUE NOT NULL,
    region     VARCHAR(100),
    population INTEGER,
    lat        NUMERIC(8, 5),
    lng        NUMERIC(8, 5)
);
"""

SQL_CREATE_WEATHER_RISK = """
CREATE TABLE IF NOT EXISTS weather_risk (
    id                   SERIAL PRIMARY KEY,
    city                 VARCHAR(100) NOT NULL,
    date                 DATE NOT NULL,
    temp_max             NUMERIC(5, 2),
    temp_min             NUMERIC(5, 2),
    precipitation        NUMERIC(6, 2),
    windspeed_max        NUMERIC(6, 2),
    windgusts_max        NUMERIC(6, 2),
    weathercode          INTEGER,
    precipitation_hours  NUMERIC(5, 2),
    temp_range           NUMERIC(5, 2),
    is_rainy             BOOLEAN,
    is_stormy            BOOLEAN,
    wind_category        VARCHAR(20),
    score_chaleur        INTEGER,
    score_vent           INTEGER,
    score_pluie          INTEGER,
    risk_score           INTEGER,
    risk_level           VARCHAR(20),
    UNIQUE (city, date)
);
"""


# ─────────────────────────────────────────────
# Fonction : creer les tables
# ─────────────────────────────────────────────

def creer_tables(engine):
    """Cree les tables cities et weather_risk si elles n'existent pas."""
    with engine.connect() as conn:
        conn.execute(text(SQL_CREATE_CITIES))
        conn.execute(text(SQL_CREATE_WEATHER_RISK))
        conn.commit()
    print("  Tables creees (ou deja existantes)")


# ─────────────────────────────────────────────
# Fonction : charger les villes
# ─────────────────────────────────────────────

def charger_cities(df, engine):
    """
    Insere les villes uniques dans la table cities.
    Ignore les doublons (ON CONFLICT DO NOTHING).
    """
    villes = df[["city", "region", "population", "lat", "lng"]].drop_duplicates(subset=["city"])

    inseres = 0
    with engine.connect() as conn:
        for _, row in villes.iterrows():
            sql = text("""
                INSERT INTO cities (city, region, population, lat, lng)
                VALUES (:city, :region, :population, :lat, :lng)
                ON CONFLICT (city) DO NOTHING
            """)
            conn.execute(sql, {
                "city":       row["city"],
                "region":     row["region"],
                "population": int(row["population"]),
                "lat":        float(row["lat"]),
                "lng":        float(row["lng"]),
            })
            inseres += 1
        conn.commit()

    print(f"  {inseres} villes traitees dans la table cities")


# ─────────────────────────────────────────────
# Fonction : charger les previsions meteo
# ─────────────────────────────────────────────

def charger_weather_risk(df, engine):
    """
    Insere les previsions dans weather_risk.
    Si (city, date) existe deja -> met a jour les valeurs (upsert).
    """
    inseres  = 0
    maj      = 0

    with engine.connect() as conn:
        for _, row in df.iterrows():
            sql = text("""
                INSERT INTO weather_risk (
                    city, date, temp_max, temp_min, precipitation,
                    windspeed_max, windgusts_max, weathercode, precipitation_hours,
                    temp_range, is_rainy, is_stormy, wind_category,
                    score_chaleur, score_vent, score_pluie, risk_score, risk_level
                )
                VALUES (
                    :city, :date, :temp_max, :temp_min, :precipitation,
                    :windspeed_max, :windgusts_max, :weathercode, :precipitation_hours,
                    :temp_range, :is_rainy, :is_stormy, :wind_category,
                    :score_chaleur, :score_vent, :score_pluie, :risk_score, :risk_level
                )
                ON CONFLICT (city, date) DO UPDATE SET
                    temp_max            = EXCLUDED.temp_max,
                    temp_min            = EXCLUDED.temp_min,
                    precipitation       = EXCLUDED.precipitation,
                    windspeed_max       = EXCLUDED.windspeed_max,
                    windgusts_max       = EXCLUDED.windgusts_max,
                    weathercode         = EXCLUDED.weathercode,
                    precipitation_hours = EXCLUDED.precipitation_hours,
                    temp_range          = EXCLUDED.temp_range,
                    is_rainy            = EXCLUDED.is_rainy,
                    is_stormy           = EXCLUDED.is_stormy,
                    wind_category       = EXCLUDED.wind_category,
                    score_chaleur       = EXCLUDED.score_chaleur,
                    score_vent          = EXCLUDED.score_vent,
                    score_pluie         = EXCLUDED.score_pluie,
                    risk_score          = EXCLUDED.risk_score,
                    risk_level          = EXCLUDED.risk_level
            """)
            result = conn.execute(sql, {
                "city":                row["city"],
                "date":                row["date"],
                "temp_max":            float(row["temp_max"]),
                "temp_min":            float(row["temp_min"]),
                "precipitation":       float(row["precipitation"]),
                "windspeed_max":       float(row["windspeed_max"]),
                "windgusts_max":       float(row["windgusts_max"]),
                "weathercode":         int(row["weathercode"]) if pd.notna(row["weathercode"]) else None,
                "precipitation_hours": float(row["precipitation_hours"]),
                "temp_range":          float(row["temp_range"]),
                "is_rainy":            bool(row["is_rainy"]),
                "is_stormy":           bool(row["is_stormy"]),
                "wind_category":       row["wind_category"],
                "score_chaleur":       int(row["score_chaleur"]),
                "score_vent":          int(row["score_vent"]),
                "score_pluie":         int(row["score_pluie"]),
                "risk_score":          int(row["risk_score"]),
                "risk_level":          row["risk_level"],
            })
            # rowcount=1 = insert, rowcount=0 = update (ON CONFLICT)
            if result.rowcount == 1:
                inseres += 1
            else:
                maj += 1

        conn.commit()

    print(f"  {inseres} lignes inserees | {maj} lignes mises a jour")


# ─────────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────────

def load_data():
    """
    Orchestre le chargement complet :
      1. Connexion a PostgreSQL
      2. Creation des tables
      3. Chargement cities + weather_risk
    """
    chemin_gold = os.path.join(GOLD_DIR, "weather_risk.csv")

    if not os.path.exists(chemin_gold):
        print("[ERREUR] weather_risk.csv introuvable.")
        print("Lance d'abord : python main.py")
        return

    print("\n=== Chargement PostgreSQL ===\n")

    # Lire le fichier gold
    df = pd.read_csv(chemin_gold)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    print(f"  {len(df)} lignes lues depuis {chemin_gold}")

    # Connexion
    print(f"  Connexion a : {DB_URL}")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  Connexion OK")
    except Exception as e:
        print(f"  [ERREUR] Impossible de se connecter : {e}")
        print("\n  Verifie que Docker est lance avec : docker-compose up -d")
        return

    # Creer les tables
    creer_tables(engine)

    # Charger les donnees
    charger_cities(df, engine)
    charger_weather_risk(df, engine)

    # Verification finale
    with engine.connect() as conn:
        nb_cities = conn.execute(text("SELECT COUNT(*) FROM cities")).scalar()
        nb_risk   = conn.execute(text("SELECT COUNT(*) FROM weather_risk")).scalar()

    print(f"\n=== Verification ===")
    print(f"  Table cities      : {nb_cities} villes")
    print(f"  Table weather_risk: {nb_risk} lignes")
    print(f"\n=== Chargement termine ===")


if __name__ == "__main__":
    load_data()
