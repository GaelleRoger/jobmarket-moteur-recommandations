"""
Extract : Offres JSearch via API (RapidAPI)
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]
sys.path.append(str(ROOT_DIR))

import os
from dotenv import load_dotenv, find_dotenv
from src.utils import fct_utiles as fct
from src.utils import save_json, DATA_RAW_JSEARCH

load_dotenv(find_dotenv())

###############################
## Déclaration des paramètres
###############################
MODE_TEST = True  # False une fois en Prod
CLIENT_SECRET = os.getenv('JS_CLIENT_SECRET')
BASE_URL = os.getenv('JS_API_URL')

PAGES_PER_ROLE = 1 if MODE_TEST else int(os.getenv('RANGE_END'))
RESULTS_PER_PAGE = 10 if MODE_TEST else int(os.getenv('MAX_PER_CODE'))
ROLES= os.getenv('LIB_ACTIVITE_INCLUS')
FRANCE = "France"

def main():
    all_results = collect_offers()
    save_offers(all_results)

def collect_offers():
    """Collecte des offres d'emploi depuis l'API JSearch (RapidAPI)"""
    roles = [r.strip() for r in ROLES.split(",")]
    all_results = []
    headers = {
        "x-rapidapi-key": CLIENT_SECRET,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }
    for role in roles:
        for page in range(1, PAGES_PER_ROLE + 1):
            params = {"query":role,"page":str(page),"num_pages":str(PAGES_PER_ROLE),"country":"fr","date_posted":"all"}
            print(f"Fetching jobs for: {role} page {page}")
            results = fct.get_data(BASE_URL,headers,params)
            if results and "data" in results:
                if len(results["data"]) == 0:
                    print("Plus d'offres → arrêt")
                    break
                all_results.extend(results["data"])
            else:
                print(f"Aucun résultat pour {role} page {page}.")

    return all_results

def save_offers(all_results):
    """Sauvegarde des offres d'emploi dans un fichier JSON"""
    if all_results:
        save_json(all_results, DATA_RAW_JSEARCH, "offres_jsearch")
        print(f"Tous les résultats ont été enregistrés dans '{DATA_RAW_JSEARCH}'.")
    else:
        print("Aucun résultat à sauvegarder.")

if __name__ == "__main__":
    main()