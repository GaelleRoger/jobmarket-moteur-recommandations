"""
Transform : Nettoyage des indicateurs de tension de France Travail
"""
import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))
from src.mongodb import get_mongo_client
from src.utils import save_json, DATA_PRO_FT

from bson import json_util
import json

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transform_tension_kpi(territory_code,db_name='job_market'):
    """Charge les indicateurs de tension depuis MongoDB"""
    logger.info("Chargement du indicateurs de tension...")

    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'tension_dept_ft'
    elif territory_code == 'REG':
        filename = 'tension_reg_ft'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    collname_raw = filename + "_raw"
    collname_pro = filename + "_pro"

    raw_coll = db[collname_raw]
    pro_coll = db[collname_pro]


    # Pipeline d'agrégation pour extraire les entrées remplies et les champs utiles
    pipeline = [
    {
        "$match": {
            "données.listeValeursParPeriode": {"$exists": True, "$ne": []} # On ne garde que les indicateurs non nuls
        }
    },
    {
        "$project": {
            "_id": 0,
            "type_territoire": 1,
            "code_territoire": 1,
            "code_ROME": 1,
            "valeurPrincipaleNombre": {
                "$arrayElemAt": ["$données.listeValeursParPeriode.valeurPrincipaleNombre", 0]
            }
        }
    }
    ]   

    # Exécution du pipeline
    docs_to_insert = list(raw_coll.aggregate(pipeline))

    # Insertion dans la collection de sortie
    if docs_to_insert:
        pro_coll.insert_many(docs_to_insert)

    logger.info(f"{len(docs_to_insert)} documents insérés dans {collname_pro}")

    client.close()

    # Convertit les documents en JSON sérialisable
    docs_serializable = json.loads(json_util.dumps(docs_to_insert))

    # Sauvegarde en JSON
    filepath = save_json(docs_serializable, DATA_PRO_FT, collname_pro)
    logger.info(f"Export JSON : {filepath.stat().st_size / 1024:.2f} KB")
    
    return filepath


if __name__ == "__main__":
    transform_tension_kpi('DEP')
    transform_tension_kpi('REG')