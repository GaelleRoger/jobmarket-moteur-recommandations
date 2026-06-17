"""
Transform : Enrichissement géographique des offres Adzuna
Utilise MongoDB geo_communes au lieu du CSV local
"""
import sys
from pathlib import Path
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))
import logging
import math
from datetime import datetime
from pymongo import UpdateOne
from src.mongodb import get_database
from src.utils import save_json, DATA_PRO_ADZUNA
from src.utils.data import deduplicate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_geo_communes(db):
    """Charge le référentiel géographique depuis MongoDB"""
    logger.info("Chargement du référentiel géographique...")
    geo_docs = list(db.geo_communes.find({}))
    logger.info(f"{len(geo_docs)} communes chargées")
    geo_by_code = {doc['_id']: doc for doc in geo_docs}
    geo_by_name = {}
    for doc in geo_docs:
        nom = doc.get('nom_standard', '').strip().lower()
        if nom:
            geo_by_name.setdefault(nom, []).append(doc)
    return geo_by_code, geo_by_name

def find_commune_by_name(commune_name, geo_by_name, region_name=None, departement_name=None):
    """Trouve une commune par son nom avec filtre département/région."""
    if not commune_name:
        return None
    
    nom_lower = commune_name.strip().lower()
    candidates = geo_by_name.get(nom_lower, [])
    
    if not candidates:
        return None
    
    if departement_name:
        dep_lower = departement_name.strip().lower()
        for c in candidates:
            if c.get('dep_nom', '').strip().lower() == dep_lower:
                return c
    
    if region_name:
        region_lower = region_name.strip().lower()
        for c in candidates:
            if c.get('reg_nom', '').strip().lower() == region_lower:
                return c
    
    return candidates[0] if len(candidates) == 1 else None

def enrich_offer(offer, geo_by_code, geo_by_name):
    """Enrichit une offre Adzuna avec données géographiques."""
    description = offer.get("description")
    if not description or not description.strip():
        return None

    area = offer.get("location", {}).get("area", [])
    if not area:
        return None

    region_name = area[1] if len(area) > 1 else None
    departement_name = area[2] if len(area) > 2 else None
    commune_name = area[-1]

    commune_doc = find_commune_by_name(commune_name, geo_by_name, region_name, departement_name)
    if not commune_doc:
        return None

    code_insee = commune_doc['_id']

    latitude = offer.get("latitude")
    longitude = offer.get("longitude")

    # Détermination du code ROME à partir du titre (insensible à la casse)
    title = offer.get("title") or ""
    title_lower = title.lower()
    rome_code = None
    if "data" and "engineer" in title_lower:
        rome_code = "M1811"
    elif "data scientist" in title_lower:
        rome_code = "M1405"
    elif "data analyst" in title_lower:
        rome_code = "M1419"
    elif "ingénieur" in title_lower and  "data" in title_lower:
        rome_code = "M1811"

    enriched = {
        "source": "adzuna",
        "id": offer.get("id"),
        "title": title,
        "description": description,
        "employer": offer.get("company", {}).get("display_name"),
        "location": offer.get("location", {}).get("display_name"),
        "latitude": latitude,
        "longitude": longitude,
        "lieuTravail": {
            "codeReg": commune_doc.get('reg_code'),
            "libReg": commune_doc.get('reg_nom'),
            "codeDep": commune_doc.get('dep_code'),
            "libDep": commune_doc.get('dep_nom'),
            "codeCom": code_insee,
            "libCom": commune_doc.get('nom_standard'),
            # "typeGeo": commune_doc.get('typecom'),
            "codePostal": str(int(commune_doc.get('code_postal'))) if commune_doc.get('code_postal') else None
        },
        "apply_link": offer.get("redirect_url"),
        "posted_at": offer.get("created"),
        "indexed_in_es": False,
    }

    # On n'ajoute romeCode que s'il a été déterminé
    if rome_code:
        enriched["romeCode"] = rome_code

    return enriched


def export_offres_enrichies(offres, stats):
    """Exporte les offres enrichies en JSON"""
    def clean(v):
        """Convertit les valeurs NaN en None récursivement."""
        if isinstance(v, float) and math.isnan(v):
            return None
        if isinstance(v, dict):
            return {k: clean(val) for k, val in v.items()}
        return v
    
    export_data = {
        'metadata': {'date_export': datetime.now().isoformat(), 'nb_offres': len(offres), 'stats': stats},
        'offres': [{k: clean(v) for k, v in offre.items()} for offre in offres]
    }
    filepath = save_json(export_data, DATA_PRO_ADZUNA, "offres_adzuna_finales")
    logger.info(f"Export JSON : {filepath.stat().st_size / 1024:.2f} KB")
    return filepath


def transform_offres_adzuna(db_name: str = "job_market"):
    """Pipeline Transform : enrichissement géographique des offres Adzuna"""
    logger.info("=== TRANSFORM : Offres Adzuna ===")
    db = get_database(db_name)
    
    try:
        geo_by_code, geo_by_name = load_geo_communes(db)
        
        logger.info("Lecture des offres brutes...")
        offres_brutes = list(db.offres_adzuna_raw.find({}))
        logger.info(f"{len(offres_brutes)} offres brutes chargées")
        
        logger.info("Enrichissement géographique...")
        offres_enrichies = []
        stats = {'total': len(offres_brutes), 'enrichies': 0, 'sans_description': 0, 'sans_commune': 0}
        
        for offre in offres_brutes:
            description = offre.get("description")
            if not description or not description.strip():
                stats['sans_description'] += 1
                continue
            
            enriched = enrich_offer(offre, geo_by_code, geo_by_name)
            if enriched:
                offres_enrichies.append(enriched)
                stats['enrichies'] += 1
            else:
                stats['sans_commune'] += 1
        
        logger.info(f"Enrichissement terminé:")
        logger.info(f"  - Total: {stats['total']}")
        logger.info(f"  - Enrichies: {stats['enrichies']}")
        logger.info(f"  - Sans description: {stats['sans_description']}")
        logger.info(f"  - Sans commune: {stats['sans_commune']}")
        
        # Déduplication
        offres_enrichies = deduplicate(offres_enrichies, 'id')
        logger.info(f"Après déduplication: {len(offres_enrichies)} offres uniques")
        
        export_offres_enrichies(offres_enrichies, stats)
        
        logger.info("Insertion dans offres_adzuna...")
        operations = [
            UpdateOne({"id": offre["id"]}, {"$set": offre}, upsert=True)
            for offre in offres_enrichies
        ]
        
        if operations:
            result = db.offres_adzuna.bulk_write(operations)
            logger.info(f"Insérés: {result.upserted_count}, Mis à jour: {result.modified_count}")
        
        count_total = db.offres_adzuna.count_documents({})
        logger.info(f"Total documents MongoDB: {count_total}")
        
        sample = db.offres_adzuna.find_one({'lieuTravail.codeCom': {'$ne': None}})
        if sample:
            lt = sample.get('lieuTravail', {})
            logger.info(f"Exemple: {sample.get('title')} - {lt.get('libCom')} ({lt.get('codeCom')})")
        
        logger.info("Transform terminé")
    finally:
        logger.info("Connexion MongoDB fermée")
        
if __name__ == "__main__":
    transform_offres_adzuna()