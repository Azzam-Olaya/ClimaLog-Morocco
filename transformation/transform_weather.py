"""
transform_weather.py
--------------------
Applique des transformations supplémentaires sur le DataFrame propre
et sauvegarde dans data/silver/weather_transformed.csv
"""

import os
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import SILVER_DIR


def transform_weather(df):
    """
    Ajoute des colonnes calculées utiles pour l'analyse :
      - temp_range    : écart entre temp_max et temp_min
      - is_rainy      : True si précipitations > 0
      - is_stormy     : True si code météo >= 95 (orage)
      - wind_category : catégorie de vent (calme / modere / fort / violent)
    """
    print("Transformation des donnees meteo...")

    # Écart de température dans la journée
    df["temp_range"] = df["temp_max"] - df["temp_min"]

    # Jour pluvieux ?
    df["is_rainy"] = df["precipitation"] > 0

    # Jour d'orage ? (codes WMO 95-99 = orages)
    df["is_stormy"] = df["weathercode"] >= 95

    # Catégorie de vent selon les rafales
    def categoriser_vent(rafales):
        if rafales >= 70:
            return "violent"
        elif rafales >= 50:
            return "fort"
        elif rafales >= 35:
            return "modere"
        else:
            return "calme"

    df["wind_category"] = df["windgusts_max"].apply(categoriser_vent)

    # Sauvegarder dans silver/weather_transformed.csv
    os.makedirs(SILVER_DIR, exist_ok=True)
    chemin = os.path.join(SILVER_DIR, "weather_transformed.csv")
    df.to_csv(chemin, index=False, encoding="utf-8")

    print(f"  Sauvegarde -> {chemin}")
    print(f"  Colonnes : {list(df.columns)}")
    return df


if __name__ == "__main__":
    from transformation.clean_data import clean_data
    df = clean_data()
    if df is not None:
        transform_weather(df)
