"""
Pipeline : copie des offres unifiées et des indicateurs de tension et d'équipements urbains vers Elasticsearch
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
from src.ELT.load.elasticsearch.load_processed_data_Mongo_to_ES import main


def index_elasticsearch() -> None:


    logger.info("=== PIPELINE : INDEX Elasticsearch ===")

    main()


if __name__ == "__main__":

    index_elasticsearch()
