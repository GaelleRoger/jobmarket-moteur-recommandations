"""
Pipeline : chargement des données brutes dans MongoDB
Regroupe les différents loaders (France Travail, Adzuna, INSEE, DataGouv).
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

# Imports des fonctions de chargement existantes
from src.ELT.load.mongodb.france_travail.offers_ft_load import (
    load_offres_raw_to_mongodb as load_ft_offres_raw,
)
from src.ELT.load.mongodb.france_travail.rome_tension_ft_load import (
    load_rome_raw_to_mongodb,
    load_tension_raw_to_mongodb,
)
from src.ELT.load.mongodb.adzuna.offers_ad_load import (
    load_offres_raw_to_mongodb as load_adzuna_offres_raw,
)
from src.ELT.load.mongodb.insee.pop_eqpt_mongodb import (
    load_eqpt_raw_to_mongodb,
    load_pop_raw_to_mongodb,
    load_eqpt_metadata_raw_to_mongodb,
)
from src.ELT.load.mongodb.datagouv.coms_load import (
    load_communes_to_mongodb,
)


def run_load_raw_mongodb(db_name: str = "job_market") -> None:
    """
    Exécute l'ensemble des chargements de données brutes dans MongoDB
    pour la base passée en paramètre.
    """

    logger.info("=== PIPELINE : LOAD RAW vers MongoDB ===")
    logger.info("Base MongoDB cible : %s", db_name)

    # 1. Référentiel géographique DataGouv
    logger.info("--- Étape 1 : Référentiel communes (DataGouv) ---")
    load_communes_to_mongodb(db_name=db_name)

    # 2. Offres France Travail
    logger.info("--- Étape 2 : Offres France Travail ---")
    load_ft_offres_raw(db_name=db_name)

    # 3. Codes ROME + indicateurs de tension France Travail
    logger.info("--- Étape 3 : Codes ROME France Travail ---")
    load_rome_raw_to_mongodb(db_name=db_name)

    logger.info("--- Étape 4 : Indicateurs de tension France Travail (DEP) ---")
    load_tension_raw_to_mongodb("DEP", db_name=db_name)

    logger.info("--- Étape 5 : Indicateurs de tension France Travail (REG) ---")
    load_tension_raw_to_mongodb("REG", db_name=db_name)

    # 4. Offres Adzuna
    logger.info("--- Étape 6 : Offres Adzuna ---")
    load_adzuna_offres_raw(db_name=db_name)

    # 5. INSEE équipements + population + métadonnées
    logger.info("--- Étape 7 : Équipements INSEE (DEP) ---")
    load_eqpt_raw_to_mongodb("DEP", db_name=db_name)

    logger.info("--- Étape 8 : Équipements INSEE (REG) ---")
    load_eqpt_raw_to_mongodb("REG", db_name=db_name)

    logger.info("--- Étape 9 : Population INSEE (DEP) ---")
    load_pop_raw_to_mongodb("DEP", db_name=db_name)

    logger.info("--- Étape 10 : Population INSEE (REG) ---")
    load_pop_raw_to_mongodb("REG", db_name=db_name)

    logger.info("--- Étape 11 : Métadonnées équipements INSEE ---")
    load_eqpt_metadata_raw_to_mongodb(db_name=db_name)

    logger.info("=== PIPELINE TERMINÉ : LOAD RAW vers MongoDB ===")


if __name__ == "__main__":
    # Permet d'éventuellement passer le nom de la base en argument plus tard
    run_load_raw_mongodb()
