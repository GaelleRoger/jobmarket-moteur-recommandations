"""
Extract : Référentiel géographique data.gouv.fr
Télécharge le CSV des communes françaises 2025
"""
import sys
from pathlib import Path
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))
import requests
import logging
from src.utils import DATA_RAW_DATAGOUV

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL stable data.gouv.fr
DATAGOUV_URL = "https://static.data.gouv.fr/resources/communes-et-villes-de-france-en-csv-excel-json-parquet-et-feather/20250221-162232/communes-france-2025.csv"
def extract_communes():
    """
    Télécharge le référentiel des communes depuis data.gouv.fr
    """
    logger.info("=== EXTRACT : Référentiel communes data.gouv.fr ===")
    
    # Créer le dossier de sortie
    output_path = DATA_RAW_DATAGOUV / "communes-france-2025.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Vérifier si déjà téléchargé
    if output_path.exists():
        logger.info(f"Fichier existant : {output_path}")
        logger.info(f"Taille : {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        return output_path
    
    # Téléchargement
    logger.info(f"Téléchargement depuis data.gouv.fr...")
    logger.info(f"URL : {DATAGOUV_URL}")
    
    try:
        response = requests.get(DATAGOUV_URL, timeout=60)
        response.raise_for_status()
        
        # Sauvegarde
        output_path.write_bytes(response.content)
        
        logger.info(f"Téléchargé : {output_path}")
        logger.info(f"Taille : {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors du téléchargement : {e}")
        raise
    
if __name__ == "__main__":
    extract_communes()
    
