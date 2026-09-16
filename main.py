"""
main.py
-------
Point d'entrée principal du projet.
Lance toutes les étapes dans l'ordre :
  1. Extraction  : cities + weather -> bronze/
  2. Transformation : clean + transform + risk -> silver/ + gold/
"""

from extraction.extract_cities import extract_cities
from extraction.extract_weather import extract_weather
from transformation.main import run as run_transformation


def main():
    print("=" * 50)
    print("  ClimaLog Morocco — Pipeline Meteo")
    print("=" * 50)

    # Étape 1 : Extraction
    print("\n[1/2] EXTRACTION\n")
    extract_cities()
    extract_weather()

    # Étape 2 : Transformation
    print("\n[2/2] TRANSFORMATION\n")
    run_transformation()

    print("\n" + "=" * 50)
    print("  Pipeline termine avec succes !")
    print("=" * 50)


if __name__ == "__main__":
    main()
