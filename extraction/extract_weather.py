"""
extract_weather.py
------------------
Lit data/bronze/cities.json, appelle l'API Open-Meteo pour chaque ville,
et sauvegarde toutes les prévisions dans data/bronze/weather_forecast.json
"""

import json
import os
import time
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    OPEN_METEO_URL, DAILY_VARIABLES, FORECAST_DAYS,
    API_TIMEOUT, API_RETRIES, BRONZE_DIR
)


def appeler_api(ville):
    """
    Appelle Open-Meteo pour une ville.
    Retourne le JSON brut ou None si toutes les tentatives échouent.
    """
    params = {
        "latitude":      ville["lat"],
        "longitude":     ville["lng"],
        "daily":         ",".join(DAILY_VARIABLES),
        "timezone":      "Africa/Casablanca",
        "forecast_days": FORECAST_DAYS,
    }

    for tentative in range(1, API_RETRIES + 1):
        try:
            reponse = requests.get(OPEN_METEO_URL, params=params, timeout=API_TIMEOUT)
            reponse.raise_for_status()
            donnees = reponse.json()

            if "daily" not in donnees:
                print(f"  [ERREUR] {ville['city']} : reponse inattendue")
                return None

            return donnees

        except requests.Timeout:
            print(f"  [TIMEOUT] {ville['city']} : tentative {tentative}/{API_RETRIES}")

        except requests.HTTPError as e:
            print(f"  [ERREUR HTTP] {ville['city']} : {e}")
            return None

        except requests.RequestException as e:
            print(f"  [ERREUR RESEAU] {ville['city']} : tentative {tentative}/{API_RETRIES} - {e}")

        if tentative < API_RETRIES:
            time.sleep(5)

    print(f"  [ECHEC] {ville['city']} : abandon apres {API_RETRIES} tentatives")
    return None


def extract_weather():
    """
    Pour chaque ville dans cities.json, appelle l'API et
    sauvegarde toutes les prévisions dans weather_forecast.json
    """
    chemin_cities = os.path.join(BRONZE_DIR, "cities.json")

    if not os.path.exists(chemin_cities):
        print("[ERREUR] cities.json introuvable. Lance d'abord extract_cities.py")
        return

    with open(chemin_cities, "r", encoding="utf-8") as f:
        villes = json.load(f)

    print(f"\nExtraction meteo pour {len(villes)} villes...")

    toutes_previsions = []
    succes = 0
    echecs = 0

    for ville in villes:
        donnees = appeler_api(ville)

        if donnees is None:
            echecs += 1
            continue

        # On ajoute les infos de la ville à chaque enregistrement
        toutes_previsions.append({
            "city":       ville["city"],
            "slug":       ville["slug"],
            "region":     ville["region"],
            "population": ville["population"],
            "lat":        ville["lat"],
            "lng":        ville["lng"],
            "forecast":   donnees["daily"],
        })

        print(f"  [OK] {ville['city']}")
        succes += 1

    # Sauvegarder dans bronze/weather_forecast.json
    chemin_forecast = os.path.join(BRONZE_DIR, "weather_forecast.json")
    with open(chemin_forecast, "w", encoding="utf-8") as f:
        json.dump(toutes_previsions, f, ensure_ascii=False, indent=2)

    print(f"\nResultat : {succes} OK | {echecs} echecs")
    print(f"Sauvegarde -> {chemin_forecast}")
    return toutes_previsions


if __name__ == "__main__":
    extract_weather()
