"""
Transform : Enrichissement géographique des offres France Travail
"""
import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_path))

import logging
import re
import math
from datetime import datetime
from pymongo import UpdateOne
from src.mongodb import get_mongo_client, get_database
from src.utils.geo_mapping import get_commune_rattachement
from src.utils import save_json, DATA_PRO_FT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_geo_communes(db):
    """Charge le référentiel géographique depuis MongoDB (geo_communes)"""
    logger.info("Chargement du référentiel géographique...")
    
    geo_docs = list(db.geo_communes.find({}))
    logger.info(f"{len(geo_docs)} communes chargées")
    
    # Index par code INSEE
    geo_by_code = {doc['_id']: doc for doc in geo_docs}
    
    # Régions uniques
    regions_uniques = {}
    for doc in geo_docs:
        code_reg = doc.get('reg_code') 
        if code_reg and code_reg not in regions_uniques:
            regions_uniques[code_reg] = {
                'code_reg': code_reg,
                'lib_reg': doc.get('reg_nom')  
            }
    
    return geo_by_code, regions_uniques


def analyser_localisation(offre, geo_by_code, regions_uniques):
    """
    Analyse la localisation d'une offre et détermine sa granularité.
    Gère automatiquement le rattachement des arrondissements aux communes mères.
    
    Returns: 
        tuple: (granularite, code_commune, code_dept, code_reg, libelle_original)
    """
    lieu = offre.get('lieuTravail', {})
    if not isinstance(lieu, dict):
        return ('inconnu', None, None, None, None)
    
    libelle = lieu.get('libelle', '').strip()
    
    # Cas 1: Code commune fourni
    code_commune = lieu.get('commune')
    if code_commune:
        # Rattacher les arrondissements aux communes mères (ex:75101 → 75056)
        code_commune = get_commune_rattachement(code_commune)
        return ('commune', code_commune, None, None, libelle)
    
    # Cas 2: Département (format "75 - Paris" ou "69 - Rhône")
    match_dept = re.match(r'^(\d{2,3})\s*-', libelle)
    if match_dept:
        code_dept = match_dept.group(1)
        return ('departement', None, code_dept, None, libelle)
    
    # Cas 3: Région (recherche dans le libellé)
    libelle_lower = libelle.lower()
    for code_reg, region_info in regions_uniques.items():
        lib_reg = region_info['lib_reg']
        if lib_reg and lib_reg.lower() in libelle_lower:
            return ('region', None, None, code_reg, libelle)
    
    # Cas 4: National
    if libelle_lower in ['france', 'france entière', 'national']:
        return ('national', None, None, None, libelle)
    
    # Cas 5: Étranger
    pays_etrangers = ['luxembourg', 'belgique', 'suisse', 'allemagne', 'espagne', 
                      'italie', 'royaume-uni', 'angleterre', 'pays-bas']
    for pays in pays_etrangers:
        if pays in libelle_lower:
            return ('etranger', None, None, None, libelle)
    
    # Cas 6: Inconnu
    return ('inconnu', None, None, None, libelle)

def restructurer_lieu_travail(offre, granularite, code_commune, code_dept, code_reg, libelle_original, geo_by_code):
    """
    Restructure le champ lieuTravail avec les données géographiques enrichies.
    Utilise le nouveau schéma geo_communes (data.gouv.fr).
    """
    lieu_original = offre.get('lieuTravail', {})
    if not isinstance(lieu_original, dict):
        lieu_original = {}
    
    # Structure de base du nouveau lieu
    nouveau_lieu = {
        'codeReg': None,
        'libReg': None,
        'codeDep': None,
        'libDep': None,
        'codeCom': None,
        'libCom': None,
        # 'typeGeo': None,
        # 'codeComRattachement': None,  
        'latitude': lieu_original.get('latitude'),
        'longitude': lieu_original.get('longitude'),
        'codePostal': lieu_original.get('codePostal'),
        'libelleOriginal': libelle_original
    }
    
    # Cas 1: Granularité commune
    if granularite == 'commune' and code_commune:
        geo_info = geo_by_code.get(code_commune)
        if geo_info:
            nouveau_lieu.update({
                'codeReg': geo_info.get('reg_code'),           
                'libReg': geo_info.get('reg_nom'),             
                'codeDep': geo_info.get('dep_code'),           
                'libDep': geo_info.get('dep_nom'),             
                'codeCom': code_commune,
                'libCom': geo_info.get('nom_standard'),        
                'typeGeo': geo_info.get('typecom'),            
                #'codeComRattachement': None                    
            })
            
            # Ajouter lat/long du centroïde si non présentes
            if not nouveau_lieu['latitude']:
                nouveau_lieu['latitude'] = geo_info.get('latitude_centre')
            if not nouveau_lieu['longitude']:
                nouveau_lieu['longitude'] = geo_info.get('longitude_centre')
    
    # Cas 2: Granularité département
    elif granularite == 'departement' and code_dept:
        for geo_code, geo_info in geo_by_code.items():
            if geo_info.get('dep_code') == code_dept:         
                nouveau_lieu.update({
                    'codeReg': geo_info.get('reg_code'),       
                    'libReg': geo_info.get('reg_nom'),         
                    'codeDep': code_dept,
                    'libDep': geo_info.get('dep_nom')          
                })
                break
    
    # Cas 3: Granularité région
    elif granularite == 'region' and code_reg:
        for geo_code, geo_info in geo_by_code.items():
            if geo_info.get('reg_code') == code_reg:          
                nouveau_lieu.update({
                    'codeReg': code_reg,
                    'libReg': geo_info.get('reg_nom')          
                })
                break
    
    return nouveau_lieu


def export_offres_enrichies(offres, stats):
    """Exporte les offres enrichies en JSON pour vérification"""
    offres_serialisables = []
    for offre in offres:
        offre_copy = offre.copy()
        if '_id' in offre_copy:
            del offre_copy['_id']
        
        offre_clean = {}
        for key, value in offre_copy.items():
            if isinstance(value, float):
                offre_clean[key] = None if math.isnan(value) else value
            elif isinstance(value, dict):
                offre_clean[key] = {
                    k: (None if isinstance(v, float) and math.isnan(v) else v)
                    for k, v in value.items()
                }
            else:
                offre_clean[key] = value
        
        offres_serialisables.append(offre_clean)
    
    export_data = {
        'metadata': {
            'date_export': datetime.now().isoformat(),
            'nb_offres': len(offres),
            'stats': stats
        },
        'offres': offres_serialisables
    }
    
    filepath = save_json(export_data, DATA_PRO_FT, "offres_ft_finales")
    logger.info(f"Export JSON : {filepath.stat().st_size / 1024:.2f} KB")
    
    return filepath


def transform_offres_enrichies(db_name: str = "job_market"):
    """Pipeline Transform : enrichissement géographique des offres France Travail"""
    logger.info("=== TRANSFORM : Offres France Travail ===")
    
    db = get_database(db_name)
    
    try:
        geo_by_code, regions_uniques = load_geo_communes(db)
        
        logger.info("Lecture des offres brutes...")
        offres_brutes = list(db.offres_ft_raw.find({}))
        logger.info(f"{len(offres_brutes)} offres brutes chargées")
        
        logger.info("Enrichissement géographique...")
        offres_enrichies = []
        stats = {
            'total': len(offres_brutes),
            'commune': 0,
            'departement': 0,
            'region': 0,
            'national': 0,
            'etranger': 0,
            'inconnu': 0
        }
        
        for offre in offres_brutes:
            offre_copie = offre.copy()
            
            granularite, code_commune, code_dept, code_reg, libelle_original = analyser_localisation(
                offre_copie, geo_by_code, regions_uniques
            )
            
            stats[granularite] = stats.get(granularite, 0) + 1
            
            nouveau_lieu = restructurer_lieu_travail(
                offre_copie, granularite, code_commune, code_dept, code_reg, libelle_original, geo_by_code
            )
            
            offre_copie['lieuTravail'] = nouveau_lieu
            offre_copie['indexed_in_es'] = False
            offre_copie['granularite_geo'] = granularite
            
            if granularite not in ['etranger', 'national']:
                offres_enrichies.append(offre_copie)
        
        logger.info(f"Enrichissement terminé:")
        logger.info(f"  - Total: {stats['total']}")
        logger.info(f"  - Commune: {stats['commune']}")
        logger.info(f"  - Département: {stats['departement']}")
        logger.info(f"  - Région: {stats['region']}")
        logger.info(f"  - National: {stats['national']} (filtrées)")
        logger.info(f"  - Étranger: {stats['etranger']} (filtrées)")
        logger.info(f"  - Inconnu: {stats['inconnu']}")
        logger.info(f"  - Offres finales: {len(offres_enrichies)}")
        
        export_offres_enrichies(offres_enrichies, stats)
        
        logger.info("Insertion dans offres_france_travail...")
        operations = []
        for offre in offres_enrichies:
            offre_clean = offre.copy()
            if '_id' in offre_clean:
                del offre_clean['_id']
            
            operations.append(
                UpdateOne(
                    {"_id": offre_clean["id"]},
                    {"$set": offre_clean},
                    upsert=True
                )
            )
        
        if operations:
            result = db.offres_france_travail.bulk_write(operations)
            logger.info(f"Insérés: {result.upserted_count}, Mis à jour: {result.modified_count}")
        
        count_total = db.offres_france_travail.count_documents({})
        logger.info(f"Total documents MongoDB: {count_total}")
        
        sample = db.offres_france_travail.find_one({'lieuTravail.codeCom': {'$ne': None}})
        if sample:
            lt = sample.get('lieuTravail', {})
            logger.info(f"Exemple: {sample.get('intitule')} - {lt.get('libCom')} ({lt.get('codeCom')})")
        
        logger.info("Transform terminé")
        
    finally:
        logger.info("Connexion MongoDB fermée")


if __name__ == "__main__":
    transform_offres_enrichies()