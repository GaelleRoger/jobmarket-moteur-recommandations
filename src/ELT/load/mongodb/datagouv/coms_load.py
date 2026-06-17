"""
Load : Référentiel géographique vers MongoDB
Charge le CSV data.gouv.fr dans la collection geo_communes
Remplace l'ancienne collection geo_reference
"""
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(src_path))
from src.mongodb import get_mongo_client
from src.utils import DATA_RAW_DATAGOUV

import pandas as pd
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_communes_to_mongodb(db_name: str = "job_market"):
    """
    Charge le référentiel des communes dans MongoDB
    
    Args:
        db_name: Nom de la base de données
        
    Collection créée:
        - geo_communes (remplace geo_reference)
    """
    logger.info("=== LOAD : Référentiel communes vers MongoDB ===")
    
    # Chargement du CSV
    csv_path = DATA_RAW_DATAGOUV / "communes-france-2025.csv"
    
    if not csv_path.exists():
        logger.error(f"Fichier introuvable : {csv_path}")
        logger.error("Lancez d'abord Extract : python src/ELT/Extract/DataGouv/coms_extract.py")
        return
    
    logger.info(f"Chargement du CSV : {csv_path}")
    
    df = pd.read_csv(
        csv_path,
        dtype={
            'code_insee': str,
            'dep_code': str,
            'reg_code': str,
            'code_postal': str,
            'canton_code': str,
            'epci_code': str
        },
        low_memory=False
    )
    
    logger.info(f"{len(df)} communes chargées depuis le CSV")
    
    # Sélection des colonnes utiles
    colonnes_utiles = [
        'code_insee',           # Clé primaire
        'nom_standard',         # Nom avec article
        'nom_sans_pronom',      # Nom sans article
        'typecom',              # Type (COM uniquement dans cette source)
        'typecom_texte',        # Type en texte
        'reg_code',             # Code région
        'reg_nom',              # Nom région
        'dep_code',             # Code département
        'dep_nom',              # Nom département
        'code_postal',          # Code postal principal
        'codes_postaux',        # Tous les codes postaux
        'latitude_centre',      # Latitude centroïde
        'longitude_centre',     # Longitude centroïde
        'latitude_mairie',      # Latitude mairie
        'longitude_mairie',     # Longitude mairie
        'population',           # Population
        'superficie_km2',       # Superficie
        'densite',              # Densité
        'altitude_moyenne',     # Altitude
        'zone_emploi',          # Zone d'emploi
        'epci_nom',             # EPCI
        'grille_densite_texte', # Densité
        'gentile'               # Gentilé
    ]
    
    # Filtrage des colonnes existantes
    colonnes_disponibles = [col for col in colonnes_utiles if col in df.columns]
    df_filtered = df[colonnes_disponibles].copy()
    
    logger.info(f"{len(colonnes_disponibles)} colonnes sélectionnées")
    
    # Renommage _id pour MongoDB
    df_filtered.rename(columns={'code_insee': '_id'}, inplace=True)
    
    # Converssion en dict
    communes = df_filtered.to_dict('records')
    
    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Remplacer les anciennes collections
    logger.info("Suppression des anciennes collections...")
    db.geo_reference.drop()
    logger.info("geo_reference supprimée")
    
    db.geo_communes.drop()
    logger.info("geo_communes supprimée (si existante)")
    
    # Insertion
    logger.info(f"Insertion de {len(communes)} communes dans geo_communes...")
    db.geo_communes.insert_many(communes)
    
    # Création des index
    logger.info("Création des index...")
    db.geo_communes.create_index("_id")  # Code INSEE (déjà créé par défaut)
    db.geo_communes.create_index("nom_standard")
    db.geo_communes.create_index([("dep_code", 1)])
    db.geo_communes.create_index([("reg_code", 1)])
    
    logger.info("Index créés")
    
    # Statistiques
    total = db.geo_communes.count_documents({})
    
    logger.info("Statistiques de chargement :")
    logger.info(f"Total communes : {total:,}")
    
    logger.info(f"{total:,} communes insérées dans geo_communes")
    client.close()

if __name__ == "__main__":
    load_communes_to_mongodb()