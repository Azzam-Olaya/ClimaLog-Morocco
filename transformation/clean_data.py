"""
clean_data.py
-------------
Lit weather_forecast.json (bronze) et retourne un DataFrame pandas propre.
"""

import json
import os
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import BRONZE_DIR


def clean_data():
    """
    Lit bronze/weather_forecast.json, transforme en DataFrame,
    applique les règles de nettoyage et retourne le DataFrame propre.
    """
    chemin = os.path.join(BRONZE_DIR, "weather_forecast.json")

    if not os.path.exists(chemin):
        print("[ERREUR] weather_forecast.json introuvable.")
        return None

    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    print(f"Nettoyage de {len(donnees)} villes...")

    # Construire un DataFrame : une ligne par ville par jour
    lignes = []
    for ville in donnees:
        forecast = ville["forecast"]
        nb_jours = len(forecast["time"])

        for i in range(nb_jours):
            lignes.append({
                "city":              ville["city"],
                "region":            ville["region"],
                "population":        ville["population"],
                "lat":               ville["lat"],
                "lng":               ville["lng"],
                "date":              forecast["time"][i],
                "temp_max":          forecast["temperature_2m_max"][i],
                "temp_min":          forecast["temperature_2m_min"][i],
                "precipitation":     forecast["precipitation_sum"][i],
                "windspeed_max":     forecast["windspeed_10m_max"][i],
                "windgusts_max":     forecast["windgusts_10m_max"][i],
                "weathercode":       forecast["weathercode"][i],
                "precipitation_hours": forecast["precipitation_hours"][i],
            })

    df = pd.DataFrame(lignes)

    # Règle 1 : convertir date en type date
    df["date"] = pd.to_datetime(df["date"])

    # Règle 2 : forcer les types numériques
    cols_numeriques = ["temp_max", "temp_min", "precipitation",
                       "windspeed_max", "windgusts_max", "precipitation_hours"]
    for col in cols_numeriques:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["weathercode"] = pd.to_numeric(df["weathercode"], errors="coerce").astype("Int64")

    # Règle 3 : supprimer les lignes sans température
    avant = len(df)
    df = df.dropna(subset=["temp_max", "temp_min"])
    if len(df) < avant:
        print(f"  {avant - len(df)} ligne(s) supprimee(s) (temperature manquante)")

    # Règle 4 : valeurs négatives impossibles -> 0
    df["precipitation"]       = df["precipitation"].clip(lower=0)
    df["precipitation_hours"] = df["precipitation_hours"].clip(lower=0)

    # Règle 5 : supprimer les doublons
    avant = len(df)
    df = df.drop_duplicates(subset=["city", "date"])
    if len(df) < avant:
        print(f"  {avant - len(df)} doublon(s) supprime(s)")

    # Règle 6 : trier
    df = df.sort_values(["city", "date"]).reset_index(drop=True)

    print(f"  {len(df)} lignes propres ({df['city'].nunique()} villes x {df['date'].nunique()} jours)")
    return df


if __name__ == "__main__":
    clean_data()
