"""
Pipeline : enrichissement des offres d'emploi unifiées avec des embeddings
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
from src.features.enrich_embeddings import generate_and_store_embeddings


def embeddings(
    db_name: str = "job_market",
    collection_name: str = "offres_unified",
    batch_size: int = 32
) -> None:


    logger.info("=== PIPELINE : EMBEDDINGS ===")
    logger.info("Base MongoDB cible : %s", db_name)

    generate_and_store_embeddings()


if __name__ == "__main__":
    # Permet d'éventuellement passer le nom de la base en argument plus tard
    embeddings()