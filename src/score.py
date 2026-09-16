"""
score.py
--------
Etape 4 - Enrichissement Gold

Ce script :
  1. Lit le fichier Parquet silver du jour
  2. Calcule un score de risque logistique (0 a 10) pour chaque ligne
  3. Ajoute un niveau de risque lisible (faible / modere / eleve / critique)
  4. Sauvegarde le resultat dans data/gold/

Comment fonctionne le score ?
------------------------------
Le score final est la somme de 3 sous-scores :
  - Score chaleur  (0 a 4 points) : basé sur temp_max
  - Score vent     (0 a 3 points) : basé sur rafales_kmh
  - Score pluie    (0 a 3 points) : basé sur pluie_mm et code_meteo

Total : 0 = aucun risque, 10 = risque maximum

Niveaux :
  0.0 - 2.9  -> faible
  3.0 - 4.9  -> modere
  5.0 - 7.4  -> eleve
  7.5 - 10.0 -> critique
"""

import os
import pandas as pd
from datetime import datetime, timezone


# ─────────────────────────────────────────────
# Seuils de risque (calibrés sur les données réelles du Maroc)
# ─────────────────────────────────────────────

# Chaleur : risque logistique (conducteurs, marchandises périssables)
# temp_max >= 38°C -> score 4 (critique)
# temp_max >= 35°C -> score 3
# temp_max >= 32°C -> score 2
# temp_max >= 28°C -> score 1
# temp_max <  28°C -> score 0

def score_chaleur(temp_max):
    """
    Retourne un score entre 0 et 4 selon la température maximale.
    Plus il fait chaud, plus le risque logistique est élevé.
    """
    if temp_max >= 38:
        return 4
    elif temp_max >= 35:
        return 3
    elif temp_max >= 32:
        return 2
    elif temp_max >= 28:
        return 1
    else:
        return 0


# Vent : risque pour les camions et livraisons
# rafales >= 70 km/h -> score 3 (dangereux)
# rafales >= 50 km/h -> score 2
# rafales >= 35 km/h -> score 1
# rafales <  35 km/h -> score 0

def score_vent(rafales_kmh):
    """
    Retourne un score entre 0 et 3 selon les rafales de vent.
    """
    if rafales_kmh >= 70:
        return 3
    elif rafales_kmh >= 50:
        return 2
    elif rafales_kmh >= 35:
        return 1
    else:
        return 0


# Pluie : risque glissance, visibilité, retards
# pluie >= 10 mm OU code orage (95-99) -> score 3
# pluie >= 5  mm OU code averses (80-82) -> score 2
# pluie >= 1  mm -> score 1
# pluie <  1  mm -> score 0

def score_pluie(pluie_mm, code_meteo):
    """
    Retourne un score entre 0 et 3 selon les précipitations et le code météo.

    Codes météo WMO importants :
      0-3   : ciel clair à nuageux
      51-67 : bruine et pluie légère
      71-77 : neige
      80-82 : averses
      95-99 : orages
    """
    code = int(code_meteo) if pd.notna(code_meteo) else 0

    if pluie_mm >= 10 or code >= 95:
        return 3
    elif pluie_mm >= 5 or code in range(80, 83):
        return 2
    elif pluie_mm >= 1:
        return 1
    else:
        return 0


# ─────────────────────────────────────────────
# Fonction : calculer le niveau de risque
# ─────────────────────────────────────────────

def niveau_risque(score):
    """
    Convertit un score numérique en niveau lisible.

    0.0 - 2.9  -> faible
    3.0 - 4.9  -> modere
    5.0 - 7.4  -> eleve
    7.5 - 10.0 -> critique
    """
    if score >= 7.5:
        return "critique"
    elif score >= 5.0:
        return "eleve"
    elif score >= 3.0:
        return "modere"
    else:
        return "faible"


# ─────────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────────

def run():
    """
    Orchestre l'enrichissement complet :
      1. Trouve le fichier silver du jour
      2. Calcule les scores pour chaque ligne
      3. Sauvegarde en Parquet dans data/gold/
    """
    date_du_jour = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    chemin_silver = os.path.join("data/silver", f"silver_{date_du_jour}.parquet")

    # Vérifier que le fichier silver existe
    if not os.path.exists(chemin_silver):
        print(f"[ERREUR] Fichier silver introuvable : {chemin_silver}")
        print("Lance d'abord : python -m src.clean")
        return

    print(f"\n=== Enrichissement Gold — {date_du_jour} ===\n")

    # Lire le fichier silver
    df = pd.read_parquet(chemin_silver)
    print(f"  Lignes chargees depuis silver : {len(df)}")

    # ── Calcul des 3 sous-scores ──────────────────────────────────────────

    print("  Calcul des scores de risque...")

    # Appliquer chaque fonction de score ligne par ligne
    df["score_chaleur"] = df["temp_max"].apply(score_chaleur)

    df["score_vent"] = df["rafales_kmh"].apply(score_vent)

    # score_pluie a besoin de 2 colonnes -> on utilise apply avec axis=1
    df["score_pluie"] = df.apply(
        lambda ligne: score_pluie(ligne["pluie_mm"], ligne["code_meteo"]),
        axis=1
    )

    # ── Score total et niveau ─────────────────────────────────────────────

    # Somme des 3 sous-scores (max possible = 4+3+3 = 10)
    df["score_total"] = df["score_chaleur"] + df["score_vent"] + df["score_pluie"]

    # Convertir le score en niveau lisible
    df["niveau_risque"] = df["score_total"].apply(niveau_risque)

    # ── Sauvegarder en Gold ───────────────────────────────────────────────

    dossier_gold = "data/gold"
    os.makedirs(dossier_gold, exist_ok=True)
    chemin_gold = os.path.join(dossier_gold, f"gold_{date_du_jour}.parquet")
    df.to_parquet(chemin_gold, index=False)

    # ── Résumé ────────────────────────────────────────────────────────────

    print(f"\n=== Resume ===")
    print(f"  Lignes traitees  : {len(df)}")
    print(f"  Villes           : {df['ville'].nunique()}")
    print(f"\n  Repartition des niveaux de risque :")

    # Compter combien de lignes par niveau
    comptage = df["niveau_risque"].value_counts()
    for niveau in ["critique", "eleve", "modere", "faible"]:
        nb = comptage.get(niveau, 0)
        print(f"    {niveau:<10} : {nb} jour(s)-ville(s)")

    print(f"\n  Top 5 jours les plus risques :")
    top5 = (
        df[["ville", "date", "score_total", "niveau_risque",
            "temp_max", "rafales_kmh", "pluie_mm"]]
        .sort_values("score_total", ascending=False)
        .head(5)
    )
    print(top5.to_string(index=False))

    print(f"\n  Fichier gold : {chemin_gold}")


if __name__ == "__main__":
    run()
