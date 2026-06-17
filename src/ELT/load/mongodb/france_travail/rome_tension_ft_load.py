"""
Load : Codes ROME et indicateur de tension France Travail bruts vers MongoDB
"""
import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(src_path))
from src.mongodb import get_mongo_client
from src.utils import load_latest_json, DATA_RAW_FT

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_rome_raw_to_mongodb(db_name: str = "job_market"):
    """
    Charge les codes ROME bruts depuis JSON vers MongoDB.
    
    Args:
        db_name: Nom de la base de données
        
    Collection créée:
        - codes_rome_ft_raw
    """
    logger.info("=== LOAD : Codes ROME France Travail bruts ===")
    
    # Charger le fichier le plus récent
    codes_rome, filepath = load_latest_json(DATA_RAW_FT, "codes*.json")
    
    if not codes_rome:
        logger.error("Aucun fichier trouvé. Lancez d'abord Extract.")
        return
    
    logger.info(f"Fichier chargé : {filepath}")
    logger.info(f"{len(codes_rome)} offres à insérer")
    
    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Insertion
    collection_name = 'codes_rome_ft_raw'
    logger.info(f"Insertion dans {collection_name}...")
    db[collection_name].drop()
    db[collection_name].insert_many(codes_rome)
    
    logger.info(f"{len(codes_rome)} documents insérés dans {collection_name}")
    
    client.close()

def load_tension_raw_to_mongodb(territory_code, db_name: str = "job_market"):
    """
    Charge les indicateurs de tension bruts depuis JSON vers MongoDB.
    
    Args:
        db_name: Nom de la base de données
        territory_code : "DEP" pour département ou "REG" pour région

        
    Collection créée:
        - tension_*_ft_raw
    """
    logger.info("=== LOAD : Indicateurs de tension France Travail bruts ===")

    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'tension_dept_ft'
    elif territory_code == 'REG':
        filename = 'tension_reg_ft'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    pattern = filename + "*.json"
    
    # Charger le fichier le plus récent
    tension_kpi, filepath = load_latest_json(DATA_RAW_FT, pattern)
    
    if not tension_kpi:
        logger.error("Aucun fichier trouvé. Lancez d'abord Extract.")
        return
    
    logger.info(f"Fichier chargé : {filepath}")
    logger.info(f"{len(tension_kpi)} offres à insérer")
    
    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Insertion
    collection_name = filename + "_raw"
    logger.info(f"Insertion dans {collection_name}...")
    db[collection_name].drop()
    db[collection_name].insert_many(tension_kpi)
    
    logger.info(f"{len(tension_kpi)} documents insérés dans {collection_name}")
    
    client.close()

if __name__ == "__main__":
    load_rome_raw_to_mongodb()
    load_tension_raw_to_mongodb('DEP')
    load_tension_raw_to_mongodb('REG')