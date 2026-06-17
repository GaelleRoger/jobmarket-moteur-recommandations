"""
Pipeline 03_transform : exécution des transformations MongoDB

Ce script orchestre les différents modules de transform :
- Insee : score équipements
- France Travail : offres + indicateurs de tension
- Adzuna : offres
- JSearch : offres
"""

from pathlib import Path
import logging

# Optionnel : s'assurer que src/ est bien dans le PYTHONPATH quand on lance ce script directement
import sys

CURRENT_FILE = Path(__file__).resolve()
SRC_ROOT = CURRENT_FILE.parents[2]  # src/
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Imports INSEE
from src.ELT.transform.insee.score_eqpt import load_score_mongo

# Imports France Travail
from src.ELT.transform.france_travail.offers_ft_transform import (
    transform_offres_enrichies,
)
from src.ELT.transform.france_travail.tension_ft_transform import (
    transform_tension_kpi,
)

# Imports Adzuna
from src.ELT.transform.adzuna.offers_ad_transform import (
    transform_offres_adzuna,
)

# Imports JSearch
from src.ELT.transform.jsearch.offers_jsearch_transform import (
    transform_offres_jsearch,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_insee_transforms(db_name: str = "job_market") -> None:
    """
    Lance les transformations INSEE (score équipements).
    """
    logger.info("=== PIPELINE INSEE : score équipements ===")
    # DEP et REG sont les deux valeurs supportées dans score_eqpt
    load_score_mongo("DEP", db_name=db_name)
    load_score_mongo("REG", db_name=db_name)


def run_france_travail_transforms(db_name: str = "job_market") -> None:
    """
    Lance les transformations France Travail :
    - enrichissement géographique des offres
    - indicateurs de tension (département et région)
    """
    logger.info("=== PIPELINE FRANCE TRAVAIL ===")
    transform_offres_enrichies(db_name=db_name)
    transform_tension_kpi("DEP", db_name=db_name)
    transform_tension_kpi("REG", db_name=db_name)


def run_adzuna_transforms(db_name: str = "job_market") -> None:
    """
    Lance les transformations Adzuna (enrichissement géographique des offres).
    """
    logger.info("=== PIPELINE ADZUNA ===")
    transform_offres_adzuna(db_name=db_name)


def run_jsearch_transforms(db_name: str = "job_market") -> None:
    """
    Lance les transformations JSearch (enrichissement géographique des offres).
    """
    logger.info("=== PIPELINE JSEARCH ===")
    transform_offres_jsearch(db_name=db_name)


def run_all_transforms(db_name: str = "job_market") -> None:
    """
    Pipeline complet : exécute toutes les transformations dans un ordre logique.
    """
    logger.info("=== PIPELINE 03_TRANSFORM : DÉBUT ===")

    # 1. Référentiels / indicateurs agrégés (INSEE)
    run_insee_transforms(db_name=db_name)

    # 2. Offres et indicateurs France Travail
    run_france_travail_transforms(db_name=db_name)

    # 3. Offres Adzuna
    run_adzuna_transforms(db_name=db_name)

    # 4. Offres JSearch
    run_jsearch_transforms(db_name=db_name)

    logger.info("=== PIPELINE 03_TRANSFORM : FIN ===")


if __name__ == "__main__":
    # Tu peux adapter le nom de la base ici si besoin
    run_all_transforms(db_name="job_market")
