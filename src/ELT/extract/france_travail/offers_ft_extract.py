"""
Extract : Offres France Travail 
"""
import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))

import logging
from src.sources.france_travail import fetch_offers
from src.utils import save_json, deduplicate, DATA_RAW_FT
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def extract_offres_ft(rome_codes=None, max_per_code=2000):
    """Pipeline Extract pour offres France Travail"""
    if rome_codes is None:
        rome_codes = ['M1811']   # initialement rome_codes = ['M1811']
    
    logger.info("=== EXTRACT : Offres France Travail ===")
    
    # Récupération API
    offres = fetch_offers(rome_codes, max_per_code)
    
    # Dédoublonnage
    offres_uniques = deduplicate(offres, 'id')
    
    # Sauvegarde
    filepath = save_json(offres_uniques, DATA_RAW_FT, "offres_ft")
    
    logger.info(f"Extract terminé : {len(offres_uniques)} offres")
    return filepath

if __name__ == "__main__":
    extract_offres_ft(['M1811'], max_per_code=2000)