"""
Module d'extraction des données INSEE équipements urbains et population
Télécharge uniquement les fichiers bruts sans transformation
"""
import pandas as pd
import requests
from pathlib import Path
from typing import Dict, Optional
import logging
import sys
from pathlib import Path
import os

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))
from src.sources.insee import fetch_equipements, fetch_population, fetch_eqpt_metadata
from src.utils import save_json, DATA_RAW_INSEE_EQPT
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def extract_eqpt(territory_code):
    """Télecharge les équipements urbains pour un type de territoire donné
    
    Args:
        territory_code : "DEP" pour département ou "REG" pour région
    """

    # Récupération API
    equipements = fetch_equipements(territory_code)
    
    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'eqpt_dept_insee'
    elif territory_code == 'REG':
        filename = 'eqpt_reg_insee'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    # Sauvegarde
    filepath = save_json(equipements, DATA_RAW_INSEE_EQPT, filename)
    
    logger.info(f"Extract terminé : {len(equipements)} équipements")

    return filepath


def extract_pop(territory_code):
    """Télecharge la population active pour un type de territoire donné
    
    Args:
        territory_code : "DEP" pour département ou "REG" pour région
    """

    # Récupération API
    population = fetch_population(territory_code)
    
    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'pop_dept_insee'
    elif territory_code == 'REG':
        filename = 'pop_reg_insee'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    # Sauvegarde
    filepath = save_json(population, DATA_RAW_INSEE_EQPT, filename)
    
    logger.info(f"Extract terminé : {len(population)} populations")
    
    return filepath

def extract_eqpt_metadata():
    """
    Télécharge les métadonnées des equipements INSEE
    """
    metadata_df = fetch_eqpt_metadata()
    
    output_path = Path(DATA_RAW_INSEE_EQPT)
    # Décommenter et assurer la création du dossier
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = os.path.join(output_path, "eqpt_metadata_insee.csv")
    
    # Tentative de suppression si le fichier existe pour éviter le conflit de droits
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
        except PermissionError:
            logger.error(f"Impossible de supprimer {output_file}. Vérifiez les permissions hôte.")
            raise
    
    # Sauvegarde brute
    metadata_df.to_csv(output_file, index=False)
    logger.info(f"Sauvegardé: {output_file}")
    
    return output_file


if __name__ == "__main__":
    extract_eqpt('DEP')
    extract_eqpt('REG')
    extract_pop('DEP')
    extract_pop('REG')
    extract_eqpt_metadata()