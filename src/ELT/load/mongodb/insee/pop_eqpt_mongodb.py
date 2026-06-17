"""
Module de chargement des données brutes dans MongoDB
"""
import pandas as pd
from pathlib import Path
from typing import Dict
import logging
import os
from dotenv import load_dotenv
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

import sys

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(src_path))
from src.mongodb import get_mongo_client
from src.utils import load_latest_json, DATA_RAW_INSEE_EQPT


def load_eqpt_raw_to_mongodb(territory_code, db_name: str = "job_market"):
    """
    Charge les equipements urbains bruts par territoire depuis JSON vers MongoDB.
    
    Args:
        db_name: Nom de la base de données
        territory_code : "DEP" pour département ou "REG" pour région
        
    Collection créée:
        - eqpt_*_insee_raw
    """
    logger.info("=== LOAD : Equipements INSEE bruts ===")

    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'eqpt_dept_insee'
    elif territory_code == 'REG':
        filename = 'eqpt_reg_insee'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    pattern = filename + "*.json"
    
    # Charger le fichier le plus récent
    eqpt, filepath = load_latest_json(DATA_RAW_INSEE_EQPT, pattern)
    
    if not eqpt:
        logger.error("Aucun fichier trouvé. Lancez d'abord Extract.")
        return
    
    logger.info(f"Fichier chargé : {filepath}")
    logger.info(f"{len(eqpt)} offres à insérer")
    
    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Insertion
    collection_name = filename + "_raw"
    logger.info(f"Insertion dans {collection_name}...")
    db[collection_name].drop()
    db[collection_name].insert_many(eqpt)
    
    logger.info(f"{len(eqpt)} documents insérés dans {collection_name}")
    
    client.close()

def load_pop_raw_to_mongodb(territory_code, db_name: str = "job_market"):
    """
    Charge les populations brutes par territoire depuis JSON vers MongoDB.
    
    Args:
        db_name: Nom de la base de données
        territory_code : "DEP" pour département ou "REG" pour région
        
    Collection créée:
        - eqpt_*_insee_raw
    """
    logger.info("=== LOAD : Population INSEE bruts ===")

    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'pop_dept_insee'
    elif territory_code == 'REG':
        filename = 'pop_reg_insee'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    pattern = filename + "*.json"
    
    # Charger le fichier le plus récent
    pop, filepath = load_latest_json(DATA_RAW_INSEE_EQPT, pattern)
    
    if not pop:
        logger.error("Aucun fichier trouvé. Lancez d'abord Extract.")
        return
    
    logger.info(f"Fichier chargé : {filepath}")
    logger.info(f"{len(pop)} offres à insérer")
    
    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Insertion
    collection_name = filename + "_raw"
    logger.info(f"Insertion dans {collection_name}...")
    db[collection_name].drop()
    db[collection_name].insert_many(pop)
    
    logger.info(f"{len(pop)} documents insérés dans {collection_name}")
    
    client.close()


def load_eqpt_metadata_raw_to_mongodb(db_name: str = "job_market"):
    """
    Charge les fichiers Mettadonnées des équipements bruts dans MongoDB
    
    Args:
        db_name: Nom de la base de données
        
    """
    logger.info("Chargement des métadonnées INSEE brutes dans MongoDB...")
    
    client = get_mongo_client()
    db = client[db_name]

    collection_name = 'eqpt_metadata_insee_raw'

    #filepath = Path('data/raw/insee_eqpt/eqpt_metadata_insee.csv')

    output_path = Path(DATA_RAW_INSEE_EQPT)
    filepath = os.path.join(output_path, "eqpt_metadata_insee.csv")

    # Lecture du CSV brut
    logger.info(f"Lecture de {filepath}...")
    df = pd.read_csv(filepath, dtype=str, encoding='utf-8')

    # Conversion en documents MongoDB
    documents = df.to_dict('records')
        
    # Drop + Insert (remplacement complet)
    logger.info(f"Insertion dans {collection_name}...")
    db[collection_name].drop()
    db[collection_name].insert_many(documents)
        
    logger.info(f"{len(documents)} documents insérés dans {collection_name}")
      
    client.close()
    logger.info("Chargement terminé")
    
if __name__ == "__main__":
    load_eqpt_raw_to_mongodb('DEP')
    load_eqpt_raw_to_mongodb('REG')
    load_eqpt_metadata_raw_to_mongodb()
    load_pop_raw_to_mongodb('DEP')
    load_pop_raw_to_mongodb('REG')
