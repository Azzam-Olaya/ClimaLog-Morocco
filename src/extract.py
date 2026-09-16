"""
extract.py
----------
Script principal de l'étape Bronze.

Ce script fait 3 choses pour chaque ville :
  1. Appelle l'API Open-Meteo pour récupérer les prévisions météo
  2. Ajoute des informations sur la ville (nom, région, coordonnées...)
  3. Sauvegarde le tout dans un fichier JSON dans data/bronze/

Règle importante : les fichiers bronze ne sont JAMAIS modifiés après écriture.
Si on relance le script le même jour, les fichiers existants sont ignorés.
"""

import os
import json
import time
import requests
from datetime import datetime, timezone

import pandas as pd

from src.config import (
    OPEN_METEO_URL,
    BRONZE_DIR,
    DAILY_VARIABLES,
    FORECAST_DAYS,
    API_TIMEOUT,
    API_RETRIES,
)
from src.cities_config import charger_villes


# ─────────────────────────────────────────────
# Fonction 1 : appeler l'API pour une ville
# ─────────────────────────────────────────────

def appeler_api(ville):
    """
    Appelle Open-Meteo pour une ville et retourne la réponse JSON.
    Retourne None si toutes les tentatives échouent.

    Paramètres envoyés à l'API :
      - latitude / longitude : coordonnées de la ville
      - daily               : liste des variables météo voulues
      - timezone            : fuseau horaire du Maroc
      - forecast_days       : nombre de jours de prévision
    """
    # Paramètres de la requête HTTP
    params = {
        "latitude":      ville["lat"],
        "longitude":     ville["lng"],
        "daily":         ",".join(DAILY_VARIABLES),
        "timezone":      "Africa/Casablanca",
        "forecast_days": FORECAST_DAYS,
    }

    # On essaie plusieurs fois en cas d'échec
    for tentative in range(1, API_RETRIES + 1):
        try:
            reponse = requests.get(OPEN_METEO_URL, params=params, timeout=API_TIMEOUT)

            # Lève une erreur si le code HTTP est 4xx ou 5xx
            reponse.raise_for_status()

            # Convertit la réponse en dictionnaire Python
            donnees = reponse.json()

            # Vérifie que la réponse contient bien les données météo
            if "daily" not in donnees:
                print(f"  [ERREUR] {ville['nom']} : réponse inattendue de l'API")
                return None

            return donnees

        except requests.Timeout:
            print(f"  [TIMEOUT] {ville['nom']} : tentative {tentative}/{API_RETRIES}")

        except requests.HTTPError as e:
            # Erreur HTTP (ex: 404, 500) → inutile de réessayer
            print(f"  [ERREUR HTTP] {ville['nom']} : {e}")
            return None

        except requests.RequestException as e:
            # Erreur réseau générique
            print(f"  [ERREUR RÉSEAU] {ville['nom']} : tentative {tentative}/{API_RETRIES} — {e}")

        # Attendre 5 secondes avant de réessayer
        if tentative < API_RETRIES:
            time.sleep(5)

    print(f"  [ÉCHEC] {ville['nom']} : abandon après {API_RETRIES} tentatives")
    return None


# ─────────────────────────────────────────────
# Fonction 2 : sauvegarder en JSON
# ─────────────────────────────────────────────

def sauvegarder_bronze(ville, donnees_api, dossier, horodatage):
    """
    Sauvegarde les données brutes dans data/bronze/YYYY-MM-DD/{slug}.json

    Structure du fichier JSON :
    {
        "_meta": { informations sur la ville et l'extraction },
        "raw":   { réponse brute de l'API, non modifiée }
    }
    """
    chemin_fichier = os.path.join(dossier, f"{ville['slug']}.json")

    # Ne pas écraser un fichier existant (idempotence)
    if os.path.exists(chemin_fichier):
        print(f"  [IGNORÉ] {ville['nom']} : fichier déjà présent")
        return "ignore"

    # Enveloppe les données avec les métadonnées de la ville
    enregistrement = {
        "_meta": {
            "extrait_le":  horodatage,
            "ville":       ville["nom"],
            "region":      ville["region"],
            "population":  ville["population"],
            "latitude":    ville["lat"],
            "longitude":   ville["lng"],
            "source":      "open-meteo.com",
        },
        "raw": donnees_api,   # données brutes de l'API, jamais modifiées
    }

    # Écriture du fichier JSON
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(enregistrement, f, ensure_ascii=False, indent=2)

    print(f"  [OK] {ville['nom']} -> {chemin_fichier}")
    return "succes"


# ─────────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────────

def run():
    """
    Orchestre l'extraction complète :
      1. Charge la liste des villes depuis ma.csv
      2. Pour chaque ville : appelle l'API et sauvegarde le JSON
      3. Affiche un résumé à la fin
    """
    # Date du jour pour nommer le sous-dossier
    date_du_jour = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    horodatage   = datetime.now(timezone.utc).isoformat()

    # Créer le dossier data/bronze/YYYY-MM-DD/ s'il n'existe pas
    dossier_bronze = os.path.join(BRONZE_DIR, date_du_jour)
    os.makedirs(dossier_bronze, exist_ok=True)

    # Charger les villes depuis ma.csv
    villes = charger_villes()

    # Compteurs pour le résumé final
    succes  = 0
    echecs  = 0
    ignores = 0

    print(f"\n=== Extraction Bronze — {date_du_jour} — {len(villes)} villes ===\n")

    for ville in villes:
        # Appel API
        donnees = appeler_api(ville)

        if donnees is None:
            echecs += 1
            continue

        # Sauvegarde
        resultat = sauvegarder_bronze(ville, donnees, dossier_bronze, horodatage)

        if resultat == "succes":
            succes += 1
        else:
            ignores += 1

    # Résumé final
    print(f"\n=== Résumé ===")
    print(f"  Succès  : {succes}")
    print(f"  Échecs  : {echecs}")
    print(f"  Ignorés : {ignores} (déjà extraits aujourd'hui)")
    print(f"  Fichiers dans : {dossier_bronze}")


# Point d'entrée : ce bloc s'exécute quand on lance
# "python src/extract.py" directement
if __name__ == "__main__":
    run()
