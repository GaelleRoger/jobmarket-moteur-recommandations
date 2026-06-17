"""
Pipeline : fusion des offres France Travail, Adzuna, Jsearch
"""

import logging
from pathlib import Path
import sys

# On se place à la racine du projet pour pouvoir importer src.*
# Ce script est dans src/pipelines/, donc la racine est 2 niveaux au-dessus
ROOT_PATH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_PATH))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports des fonctions existantes
from src.features.merge_offers import merge_collections


def merge_offers(db_name: str = "job_market") -> None:
    """
    Exécute l'ensemble des chargements de données brutes dans MongoDB
    pour la base passée en paramètre.
    """

    logger.info("=== PIPELINE : MERGE OFFERS ===")
    logger.info("Base MongoDB cible : %s", db_name)

    merge_collections(db_name=db_name)


if __name__ == "__main__":
    # Permet d'éventuellement passer le nom de la base en argument plus tard
    merge_offers()