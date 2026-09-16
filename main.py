"""
main.py
-------
Point d'entree principal du projet.
Lance toutes les etapes dans l'ordre :
  1. Extraction  : cities + weather  -> bronze/
  2. Transformation : clean + transform + risk -> silver/ + gold/
  3. Loading     : gold/ -> PostgreSQL
"""

from extraction.extract_cities import extract_cities
from extraction.extract_weather import extract_weather
from transformation.main import run as run_transformation
from loading.load_data import load_data


def main():
    print("=" * 50)
    print("  ClimaLog Morocco - Pipeline Meteo")
    print("=" * 50)

    print("\n[1/3] EXTRACTION\n")
    extract_cities()
    extract_weather()

    print("\n[2/3] TRANSFORMATION\n")
    run_transformation()

    print("\n[3/3] CHARGEMENT POSTGRESQL\n")
    load_data()

    print("\n" + "=" * 50)
    print("  Pipeline termine avec succes !")
    print("=" * 50)


if __name__ == "__main__":
    main()
