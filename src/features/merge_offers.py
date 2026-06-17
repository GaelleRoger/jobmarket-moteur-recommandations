"""
Fusion des 3 collections dans offres_unified
"""
import sys
from pathlib import Path
src_path = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(src_path))

from datetime import datetime
from src.mongodb import get_database
from src.utils import save_json
from src.utils.paths import PROJECT_ROOT

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def harmonize_ft(offer):
    """Harmonise France Travail vers schéma unifié"""
    import math
    
    entreprise = offer.get('entreprise', {})
    lieu_travail = offer.get('lieuTravail', {})
    
    # Nettoyer NaN dans lieuTravail
    lieu_travail_clean = {}
    for k, v in lieu_travail.items():
        if isinstance(v, float) and math.isnan(v):
            lieu_travail_clean[k] = None
        else:
            lieu_travail_clean[k] = v
    
    # Utiliser 'nom' en priorité, sinon 'description'
    employer = None
    if entreprise:
        employer = entreprise.get('nom') or entreprise.get('description', '')
        if employer:
            employer = employer.strip()
    
    return {
        'source': 'france_travail',
        'id': offer.get('id'),
        'title': offer.get('intitule'),
        'description': offer.get('description'),
        'employer': employer,  
        'location': lieu_travail.get('libelleOriginal'),
        'lieuTravail': lieu_travail_clean,  
        'apply_link': offer.get('origineOffre', {}).get('urlOrigine'),
        'posted_at': offer.get('dateCreation'),
        'indexed_in_es': False,
        'romeCode': offer.get('romeCode'),
        'typeContrat': offer.get('typeContrat'),
        'experienceLibelle': offer.get('experienceLibelle'),
        'salaire': offer.get('salaire'),
        'competences': offer.get('competences')
    }
    
def clean_mongodb_fields(offers):
    """Supprime les champs MongoDB non sérialisables"""
    for offer in offers:
        if '_id' in offer:
            del offer['_id']
    return offers

def merge_collections(db_name: str = "job_market"):
    """Fusionne les 3 collections dans offres_unified"""
    logger.info("=== FUSION DES COLLECTIONS ===")
    db = get_database(db_name)
    
    try:
        logger.info("Chargement...")
        ft = list(db.offres_france_travail.find({}))
        adzuna = list(db.offres_adzuna.find({}))
        jsearch = list(db.offres_jsearch.find({}))
        logger.info(f"FT: {len(ft)}, Adzuna: {len(adzuna)}, JSearch: {len(jsearch)}")
        
        logger.info("Harmonisation...")
        unified = [harmonize_ft(o) for o in ft] + adzuna + jsearch
        
        logger.info("Déduplication...")
        unique = {(o['source'], o['id']): o for o in unified}
        final = list(unique.values())
        final = clean_mongodb_fields(final)  
        logger.info(f"Uniques: {len(final)} (doublons: {len(unified) - len(final)})")
        
        # Exportation Json
        logger.info("\nExport JSON...")
        export_data = {
            'metadata': {
                'date_export': datetime.now().isoformat(),
                'nb_offres': len(final),
                'sources': {'france_travail': len(ft), 'adzuna': len(adzuna), 'jsearch': len(jsearch)}
            },
            'offres': final
        }
        output_dir = PROJECT_ROOT / "data/processed/unified"
        filepath = save_json(export_data, output_dir, "offres_unified")
        logger.info(f"Export : {filepath.stat().st_size / 1024:.2f} KB")
        
        # Insertion
        logger.info("Insertion dans offres_unified...")
        db.offres_unified.drop()
        
        if final:
            db.offres_unified.insert_many(final)
            logger.info(f"Insérés: {db.offres_unified.count_documents({})}")
        
        logger.info("\n=== FUSION TERMINÉE ===")
        
    finally:
        logger.info("Connexion fermée")

if __name__ == "__main__":
    merge_collections()