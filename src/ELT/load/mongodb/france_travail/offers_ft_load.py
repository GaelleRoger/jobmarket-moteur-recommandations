"""
Load : Offres France Travail brutes vers MongoDB
"""
import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(src_path))
import logging
from src.mongodb import get_mongo_client
from src.utils import load_latest_json, DATA_RAW_FT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_offres_raw_to_mongodb(db_name: str = "job_market"):
    """
    Charge les offres brutes depuis JSON vers MongoDB.
    
    Args:
        db_name: Nom de la base de données
        
    Collection créée:
        - offres_ft_raw
    """
    logger.info("=== LOAD : Offres France Travail brutes ===")
    
    # Charger le fichier le plus récent
    offres, filepath = load_latest_json(DATA_RAW_FT, "offres*.json")
    
    if not offres:
        logger.error("Aucun fichier trouvé. Lancez d'abord Extract.")
        return
    
    logger.info(f"Fichier chargé : {filepath}")
    logger.info(f"{len(offres)} offres à insérer")
    
    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Insertion
    collection_name = 'offres_ft_raw'
    logger.info(f"Insertion dans {collection_name}...")
    db[collection_name].drop()
    db[collection_name].insert_many(offres)
    
    logger.info(f"{len(offres)} documents insérés dans {collection_name}")
    
    client.close()

if __name__ == "__main__":
    load_offres_raw_to_mongodb()