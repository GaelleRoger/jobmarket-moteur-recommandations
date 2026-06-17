"""
Extract : Offres Adzuna via API 
"""
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))

import os
from dotenv import load_dotenv, find_dotenv
from src.utils import fct_utiles as fct
from src.utils import save_json, DATA_RAW_ADZUNA

load_dotenv(find_dotenv())

###############################
## Déclaration des paramètres
###############################
MODE_TEST = False  # False une fois en Prod
CLIENT_ID = os.getenv('AD_CLIENT_ID')
CLIENT_SECRET = os.getenv('AD_CLIENT_SECRET')
BASE_URL = os.getenv('AD_API_URL')
PAGES_PER_ROLE = 1 if MODE_TEST else int(os.getenv('RANGE_END'))
RESULTS_PER_PAGE = 50 if MODE_TEST else int(os.getenv('MAX_PER_CODE'))
ROLES= os.getenv('LIB_ACTIVITE_INCLUS')

def main():
    all_results = collect_offers()
    save_offers(all_results)

def collect_offers():
    """Collecte des offres d'emploi depuis l'API Adzuna"""
    roles = [r.strip() for r in ROLES.split(",")]
    all_results = []
    headers = {"Content-Type": "application/json"}

    for role in roles:
        params = {"app_id": CLIENT_ID,"app_key": CLIENT_SECRET,"what": role,"results_per_page": RESULTS_PER_PAGE}
        for page in range(1, PAGES_PER_ROLE + 1):
            print(f"Fetching jobs for: {role} page {page}")
            url=f"{BASE_URL}/{page}"
            results = fct.get_data(url,headers,params)
            if results and "results" in results:
                if len(results["results"]) == 0:
                    print("Plus d'offres → arrêt")
                    break
                all_results.extend(results["results"])
            else:
                print(f"Aucun résultat pour {role} page {page}.")

    return all_results

def save_offers(all_results):
    """Sauvegarde des offres d'emploi dans un fichier JSON"""
    if all_results:
        save_json(all_results, DATA_RAW_ADZUNA, "offres_adzuna")
        print(f"Tous les résultats ont été enregistrés dans '{DATA_RAW_ADZUNA}'.")
    else:
        print("Aucun résultat à sauvegarder.")

if __name__ == "__main__":
    main()