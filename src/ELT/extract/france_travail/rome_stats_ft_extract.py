"""
Extract France Travail : Référentiel des codes ROME et indicateur de tension par départemnt et région
"""
import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))

import logging
from src.sources.france_travail import fetch_rome_codes, fetch_tension_indicator
from src.utils import save_json, DATA_RAW_FT
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def extract_rome_codes():
    """Pipeline Extract pour le référentiel des codes ROME"""
    
    logger.info("=== EXTRACT : Référentiel Codes ROME ===")
    
    # Récupération API
    codes_rome = fetch_rome_codes()
    
    # Sauvegarde
    filepath = save_json(codes_rome, DATA_RAW_FT, "codes_rome")
    
    logger.info(f"Extract terminé : {len(codes_rome)} codes ROME")
    return filepath

def extract_tension_indicator(territory_code, rome_codes=None):
    """Pipeline Extract pour les indicateurs de tension"""
    
    if rome_codes is None:
        rome_codes = ['M1405','M1419','M1423','M1811','M1868','M1894','M1826','M1846','M1812','M1853','M1857']
    
    logger.info("=== EXTRACT : Indicateurs de tension  ===")
    
    # Récupération API
    tension_indic = fetch_tension_indicator(territory_code, rome_codes)

    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'tension_dept_ft'
    elif territory_code == 'REG':
        filename = 'tension_reg_ft'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"
    
    # Sauvegarde
    filepath = save_json(tension_indic, DATA_RAW_FT, filename)
    
    logger.info(f"Extract terminé : {len(tension_indic)} indicateurs de tension")
    return filepath

if __name__ == "__main__":
    extract_rome_codes()
    extract_tension_indicator('DEP')
    extract_tension_indicator('REG')