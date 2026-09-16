"""
clean.py
--------
Étape 3 — Nettoyage Silver

Ce script :
  1. Lit tous les fichiers JSON du dossier bronze/ du jour
  2. Transforme chaque fichier en tableau (DataFrame pandas)
  3. Nettoie les données (types, nulls, doublons, valeurs impossibles)
  4. Fusionne toutes les villes en un seul tableau
  5. Sauvegarde le résultat dans data/silver/silver_YYYY-MM-DD.parquet
"""


import os
import json
import pandas as pd
from datetime import datetime, timezone

from src.config import BRONZE_DIR


# ─────────────────────────────────────────────
# Fonction 1 : lire un fichier JSON bronze
# et le transformer en tableau pandas
# ─────────────────────────────────────────────

def json_vers_dataframe(chemin_fichier):
    """
    Lit un fichier JSON bronze et retourne un DataFrame pandas.

    Un fichier bronze ressemble à ceci :
    {
        "_meta": { "ville": "Casablanca", "region": "...", ... },
        "raw": {
            "daily": {
                "time":               ["2026-09-16", "2026-09-17", ...],
                "temperature_2m_max": [32.1, 30.5, ...],
                ...
            }
        }
    }

    On veut transformer ça en tableau avec une ligne par jour :
    | ville      | region | date       | temp_max | temp_min | pluie | ...
    | Casablanca | ...    | 2026-09-16 | 32.1     | 22.3     | 0.0   | ...
    | Casablanca | ...    | 2026-09-17 | 30.5     | 21.1     | 2.5   | ...
    """
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        contenu = json.load(f)

    meta  = contenu["_meta"]
    daily = contenu["raw"]["daily"]

    # Créer le DataFrame à partir des données météo journalières
    df = pd.DataFrame({
        "date":          daily["time"],
        "temp_max":      daily["temperature_2m_max"],
        "temp_min":      daily["temperature_2m_min"],
        "pluie_mm":      daily["precipitation_sum"],
        "vent_max_kmh":  daily["windspeed_10m_max"],
        "rafales_kmh":   daily["windgusts_10m_max"],
        "code_meteo":    daily["weathercode"],
        "heures_pluie":  daily["precipitation_hours"],
    })

    # Ajouter les informations de la ville sur chaque ligne
    df.insert(0, "ville",      meta["ville"])
    df.insert(1, "region",     meta["region"])
    df.insert(2, "population", meta["population"])
    df.insert(3, "latitude",   meta["latitude"])
    df.insert(4, "longitude",  meta["longitude"])

    return df


# ─────────────────────────────────────────────
# Fonction 2 : nettoyer le DataFrame
# ─────────────────────────────────────────────

def nettoyer(df):
    """
    Applique toutes les règles de nettoyage sur le DataFrame.

    Règles appliquées :
      1. Convertir la colonne 'date' en vrai type date (pas du texte)
      2. Forcer les colonnes numériques au bon type
      3. Supprimer les lignes où temp_max ou temp_min est vide (null)
      4. Remplacer les valeurs négatives de pluie par 0 (impossible physiquement)
      5. Supprimer les doublons sur (ville + date)
      6. Trier par ville puis par date
    """

    # Règle 1 : convertir 'date' de texte "2026-09-16" en type date Python
    df["date"] = pd.to_datetime(df["date"])

    # Règle 2 : forcer les types numériques
    # errors="coerce" : si une valeur ne peut pas être convertie, elle devient NaN
    colonnes_numeriques = [
        "temp_max", "temp_min", "pluie_mm",
        "vent_max_kmh", "rafales_kmh", "heures_pluie"
    ]
    for col in colonnes_numeriques:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["code_meteo"] = pd.to_numeric(df["code_meteo"], errors="coerce").astype("Int64")

    # Règle 3 : supprimer les lignes sans température (données inutilisables)
    nb_avant = len(df)
    df = df.dropna(subset=["temp_max", "temp_min"])
    nb_supprimes = nb_avant - len(df)
    if nb_supprimes > 0:
        print(f"  {nb_supprimes} ligne(s) supprimée(s) car température manquante")

    # Règle 4 : la pluie ne peut pas être négative
    df["pluie_mm"]     = df["pluie_mm"].clip(lower=0)
    df["heures_pluie"] = df["heures_pluie"].clip(lower=0)

    # Règle 5 : supprimer les doublons (même ville, même date)
    nb_avant = len(df)
    df = df.drop_duplicates(subset=["ville", "date"])
    nb_doublons = nb_avant - len(df)
    if nb_doublons > 0:
        print(f"  {nb_doublons} doublon(s) supprimé(s)")

    # Règle 6 : trier proprement
    df = df.sort_values(["ville", "date"]).reset_index(drop=True)

    return df


# ─────────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────────

def run():
    """
    Orchestre le nettoyage complet :
      1. Trouve le dossier bronze du jour
      2. Lit tous les fichiers JSON
      3. Nettoie les données
      4. Sauvegarde en Parquet dans data/silver/
    """
    date_du_jour = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dossier_bronze = os.path.join(BRONZE_DIR, date_du_jour)

    # Vérifier que le dossier bronze existe
    if not os.path.exists(dossier_bronze):
        print(f"[ERREUR] Dossier bronze introuvable : {dossier_bronze}")
        print("Lance d'abord : python -m src.extract")
        return

    # Lister tous les fichiers JSON du dossier
    fichiers_json = [
        f for f in os.listdir(dossier_bronze)
        if f.endswith(".json")
    ]

    if not fichiers_json:
        print(f"[ERREUR] Aucun fichier JSON trouvé dans {dossier_bronze}")
        return

    print(f"\n=== Nettoyage Silver — {date_du_jour} — {len(fichiers_json)} fichiers ===\n")

    # Lire chaque fichier JSON et construire un DataFrame par ville
    tous_les_df = []
    erreurs = 0

    for nom_fichier in sorted(fichiers_json):
        chemin = os.path.join(dossier_bronze, nom_fichier)
        try:
            df_ville = json_vers_dataframe(chemin)
            tous_les_df.append(df_ville)
            print(f"  [LU] {nom_fichier} — {len(df_ville)} jours")
        except Exception as e:
            print(f"  [ERREUR] {nom_fichier} : {e}")
            erreurs += 1

    if not tous_les_df:
        print("[ERREUR] Aucune donnée à nettoyer.")
        return

    # Fusionner tous les DataFrames en un seul grand tableau
    print(f"\n  Fusion de {len(tous_les_df)} villes...")
    df_complet = pd.concat(tous_les_df, ignore_index=True)
    print(f"  Lignes avant nettoyage : {len(df_complet)}")

    # Nettoyer
    df_propre = nettoyer(df_complet)
    print(f"  Lignes après nettoyage : {len(df_propre)}")

    # Sauvegarder en Parquet dans data/silver/
    dossier_silver = "data/silver"
    os.makedirs(dossier_silver, exist_ok=True)
    chemin_silver = os.path.join(dossier_silver, f"silver_{date_du_jour}.parquet")
    df_propre.to_parquet(chemin_silver, index=False)

    # Résumé final
    print(f"\n=== Résumé ===")
    print(f"  Villes traitées : {df_propre['ville'].nunique()}")
    print(f"  Lignes totales  : {len(df_propre)}")
    print(f"  Periode         : {df_propre['date'].min().date()} au {df_propre['date'].max().date()}")
    print(f"  Fichier silver  : {chemin_silver}")
    if erreurs > 0:
        print(f"  Fichiers en erreur : {erreurs}")


if __name__ == "__main__":
    run()
