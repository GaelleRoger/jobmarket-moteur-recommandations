"""
Script d'orchestration des extractions :
- INSEE (équipements, population, métadonnées)
- France Travail (codes ROME, indicateurs de tension, offres)
- Data.gouv (référentiel des communes)
- Adzuna (offres d'emploi)

À exécuter depuis la racine du projet :
    python3 -m src.pipelines.01_extract
"""

import logging
from pathlib import Path
import sys

# S'assurer que src/ est bien dans le PYTHONPATH si besoin
src_path = Path(__file__).resolve().parents[1]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

ROOT_PATH = Path(__file__).resolve().parents[2]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

# Imports depuis les modules d'extract
from src.ELT.extract.insee.pop_eqpt_insee import (  # type: ignore
    extract_eqpt,
    extract_pop,
    extract_eqpt_metadata,
)
from src.ELT.extract.datagouv.coms_extract import extract_communes  # type: ignore
from src.ELT.extract.france_travail.rome_stats_ft_extract import (  # type: ignore
    extract_rome_codes,
    extract_tension_indicator,
)
from src.ELT.extract.france_travail.offers_ft_extract import (  # type: ignore
    extract_offres_ft,
)
from src.ELT.extract.adzuna.offers_ad_extract import (  # type: ignore
    main as adzuna_main,
    collect_offers,
    save_offers,
)

from src.ELT.extract.jsearch.offers_js_extract import main as jsearch_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_insee_extracts():
    """Lance les extractions INSEE (DEP + REG + métadonnées)."""
    logger.info("=== PIPELINE INSEE ===")
    extract_eqpt("DEP")
    extract_eqpt("REG")
    extract_pop("DEP")
    extract_pop("REG")
    extract_eqpt_metadata()


def run_france_travail_extracts():
    """Lance les extractions France Travail (codes ROME, tension, offres)."""
    logger.info("=== PIPELINE FRANCE TRAVAIL ===")
    # Codes ROME et indicateurs de tension
    extract_rome_codes()
    extract_tension_indicator("DEP")
    extract_tension_indicator("REG")
    # Offres France Travail (codes par défaut dans le module)
    extract_offres_ft()


def run_datagouv_extracts():
    """Lance l'extraction du référentiel des communes data.gouv."""
    logger.info("=== PIPELINE DATAGOUV ===")
    extract_communes()


def run_adzuna_extracts():
    """
    Lance l'extraction des offres Adzuna.

    Deux options possibles :
    - utiliser la fonction main() définie dans offers_ad_extract.py
    - ou utiliser collect_offers() + save_offers() pour plus de contrôle
    """
    logger.info("=== PIPELINE ADZUNA ===")
    # Option simple : réutiliser le main existant
    adzuna_main()

    # Option plus explicite :
    # all_results = collect_offers()
    # save_offers(all_results)


def run_jsearch_extracts():
    """Lance l'extraction des offres JSearch."""
    logger.info("PIPELINE JSEARCH")
    jsearch_main()  # Appel du main du module JSearch

def run_all_pipelines():
    """Orchestre l'ensemble des pipelines d'extraction."""
    logger.info("DÉBUT DES EXTRACTIONS")
    run_insee_extracts()
    run_france_travail_extracts()
    run_datagouv_extracts()
    run_adzuna_extracts()
    #run_jsearch_extracts()  # Ajout de JSearch ici
    logger.info("=== FIN DES EXTRACTIONS ===")


if __name__ == "__main__":
    run_all_pipelines()
