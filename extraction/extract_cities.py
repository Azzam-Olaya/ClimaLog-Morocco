"""
extract_cities.py
-----------------
Lit le fichier ma.csv (SimpleMaps) et sauvegarde les villes
filtrées dans data/bronze/cities.json
"""

import json
import os
import unicodedata
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import CITIES_CSV, MIN_POPULATION, BRONZE_DIR, ROOT_DIR


def slugify(nom):
    """Transforme un nom de ville en identifiant ASCII sans accents."""
    sans_accents = unicodedata.normalize("NFKD", nom)
    ascii_nom = sans_accents.encode("ascii", "ignore").decode("ascii")
    return ascii_nom.lower().replace(" ", "_").replace("-", "_").replace("'", "")


def extract_cities():
    """
    Lit ma.csv, filtre les villes par population,
    et sauvegarde le résultat dans data/bronze/cities.json
    """
    print("Extraction des villes depuis ma.csv...")

    df = pd.read_csv(
        os.path.join(ROOT_DIR, CITIES_CSV),
        usecols=["city", "lat", "lng", "admin_name", "population"]
    )
    df = df.dropna(subset=["lat", "lng", "population"])
    df["population"] = pd.to_numeric(df["population"], errors="coerce")
    df = df[df["population"] >= MIN_POPULATION]
    df = df.sort_values("population", ascending=False)

    villes = []
    for ligne in df.itertuples():
        villes.append({
            "city":       ligne.city,
            "slug":       slugify(ligne.city),
            "lat":        round(float(ligne.lat), 5),
            "lng":        round(float(ligne.lng), 5),
            "region":     ligne.admin_name,
            "population": int(ligne.population),
        })

    # Sauvegarder dans bronze/cities.json
    os.makedirs(BRONZE_DIR, exist_ok=True)
    chemin = os.path.join(BRONZE_DIR, "cities.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(villes, f, ensure_ascii=False, indent=2)

    print(f"  {len(villes)} villes sauvegardees -> {chemin}")
    return villes


if __name__ == "__main__":
    extract_cities()
