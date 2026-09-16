"""
transformation/main.py
----------------------
Lance toutes les étapes de transformation dans l'ordre :
  1. clean_data      -> nettoie les données brutes
  2. transform_weather -> ajoute les colonnes calculées -> silver/
  3. calculate_risk  -> calcule les scores de risque   -> gold/
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformation.clean_data import clean_data
from transformation.transform_weather import transform_weather
from transformation.calculate_risk import calculate_risk


def run():
    print("=== Transformation : Clean -> Silver -> Gold ===\n")

    df = clean_data()
    if df is None:
        print("[ARRET] Nettoyage echoue.")
        return

    df = transform_weather(df)
    calculate_risk(df)

    print("\n=== Transformation terminee ===")


if __name__ == "__main__":
    run()
