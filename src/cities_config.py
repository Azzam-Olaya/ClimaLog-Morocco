"""
cities_config.py
----------------
Lit le fichier ma.csv (villes marocaines de SimpleMaps)
et retourne la liste des villes à traiter.

On garde uniquement les villes avec population >= MIN_POPULATION
pour ne pas surcharger l'API avec 120+ villes.
"""

import unicodedata
import pandas as pd
from src.config import CITIES_CSV, MIN_POPULATION


def slugify(nom):
    """
    Transforme un nom de ville en nom de fichier sans caractères spéciaux.

    Exemples :
        "Fès"        -> "fes"
        "Béni Mellal" -> "beni_mellal"
        "Laâyoune"   -> "laayoune"
    """
    # Étape 1 : décompose les lettres accentuées (é -> e + accent)
    sans_accents = unicodedata.normalize("NFKD", nom)
    # Étape 2 : garde uniquement les caractères ASCII (supprime les accents)
    ascii_nom = sans_accents.encode("ascii", "ignore").decode("ascii")
    # Étape 3 : minuscules, espaces et tirets remplacés par _
    return ascii_nom.lower().replace(" ", "_").replace("-", "_").replace("'", "")


def charger_villes():
    """
    Charge ma.csv et retourne une liste de dictionnaires.

    Chaque dictionnaire représente une ville :
    {
        "nom"        : "Casablanca",
        "slug"       : "casablanca",      <- nom de fichier safe
        "lat"        : 33.5992,
        "lng"        : -7.62,
        "region"     : "Casablanca-Settat",
        "population" : 3950000
    }
    """
    # Lire le CSV en ne gardant que les colonnes utiles
    df = pd.read_csv(
        CITIES_CSV,
        usecols=["city", "lat", "lng", "admin_name", "population"]
    )

    # Supprimer les lignes où lat, lng ou population sont vides
    df = df.dropna(subset=["lat", "lng", "population"])

    # S'assurer que la colonne population est bien un nombre
    df["population"] = pd.to_numeric(df["population"], errors="coerce")

    # Garder uniquement les grandes villes
    df = df[df["population"] >= MIN_POPULATION]

    # Trier par population décroissante (Casablanca en premier)
    df = df.sort_values("population", ascending=False)

    # Construire la liste de dictionnaires
    villes = []
    for ligne in df.itertuples():
        villes.append({
            "nom":        ligne.city,
            "slug":       slugify(ligne.city),
            "lat":        round(float(ligne.lat), 5),
            "lng":        round(float(ligne.lng), 5),
            "region":     ligne.admin_name,
            "population": int(ligne.population),
        })

    print(f"{len(villes)} villes chargées (population >= {MIN_POPULATION:,})")
    return villes
