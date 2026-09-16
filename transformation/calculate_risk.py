"""
calculate_risk.py
-----------------
Calcule le score de risque logistique pour chaque ville/jour
et sauvegarde dans data/gold/weather_risk.csv
"""

import os
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import SILVER_DIR, GOLD_DIR


def score_chaleur(temp_max):
    """Score 0-4 selon la température maximale."""
    if temp_max >= 38:   return 4
    elif temp_max >= 35: return 3
    elif temp_max >= 32: return 2
    elif temp_max >= 28: return 1
    else:                return 0


def score_vent(rafales):
    """Score 0-3 selon les rafales de vent (km/h)."""
    if rafales >= 70:   return 3
    elif rafales >= 50: return 2
    elif rafales >= 35: return 1
    else:               return 0


def score_pluie(precipitation, weathercode):
    """Score 0-3 selon les précipitations et le code météo."""
    code = int(weathercode) if pd.notna(weathercode) else 0
    if precipitation >= 10 or code >= 95: return 3
    elif precipitation >= 5 or code in range(80, 83): return 2
    elif precipitation >= 1:              return 1
    else:                                 return 0


def niveau_risque(score):
    """Convertit un score numérique en niveau lisible."""
    if score >= 7.5:   return "critique"
    elif score >= 5.0: return "eleve"
    elif score >= 3.0: return "modere"
    else:              return "faible"


def calculate_risk(df):
    """
    Ajoute les colonnes de score de risque au DataFrame
    et sauvegarde dans data/gold/weather_risk.csv
    """
    print("Calcul des scores de risque...")

    df["score_chaleur"] = df["temp_max"].apply(score_chaleur)
    df["score_vent"]    = df["windgusts_max"].apply(score_vent)
    df["score_pluie"]   = df.apply(
        lambda row: score_pluie(row["precipitation"], row["weathercode"]), axis=1
    )

    df["risk_score"] = df["score_chaleur"] + df["score_vent"] + df["score_pluie"]
    df["risk_level"] = df["risk_score"].apply(niveau_risque)

    # Sauvegarder dans gold/weather_risk.csv
    os.makedirs(GOLD_DIR, exist_ok=True)
    chemin = os.path.join(GOLD_DIR, "weather_risk.csv")
    df.to_csv(chemin, index=False, encoding="utf-8")

    # Résumé
    print(f"  Sauvegarde -> {chemin}")
    print(f"\n  Repartition des niveaux de risque :")
    for niveau in ["critique", "eleve", "modere", "faible"]:
        nb = (df["risk_level"] == niveau).sum()
        print(f"    {niveau:<10} : {nb}")

    print(f"\n  Top 5 jours les plus risques :")
    top5 = (df[["city", "date", "risk_score", "risk_level", "temp_max", "windgusts_max", "precipitation"]]
            .sort_values("risk_score", ascending=False)
            .head(5))
    print(top5.to_string(index=False))

    return df


if __name__ == "__main__":
    from transformation.clean_data import clean_data
    from transformation.transform_weather import transform_weather
    df = clean_data()
    if df is not None:
        df = transform_weather(df)
        calculate_risk(df)
