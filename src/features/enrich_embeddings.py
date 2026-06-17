"""
Pipeline de génération d'embeddings pour les offres d'emploi.
Charge les offres depuis MongoDB, génère les embeddings et met à jour la base.
"""
import sys
from pathlib import Path
src_path = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(src_path))
from typing import List, Dict
from tqdm import tqdm
from src.mongodb import get_database
from src.features.text_preparation import build_composite_text
from src.models.embeddings import generate_embeddings, get_embedding_dimension

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_texts_from_offers(offers: List[Dict]) -> tuple[List[str], List[str]]:
    """
    Prépare les textes composites à partir des offres.
    
    Args:
        offers: Liste d'offres d'emploi
        
    Returns:
        Tuple (textes valides, IDs correspondants)
    """
    texts = []
    offer_ids = []
    
    logger.info(f"Préparation des textes pour {len(offers)} offres...")
    
    for offer in tqdm(offers, desc="Préparation textes"):
        text = build_composite_text(offer)
        
        if text.strip():  # Vérification simple : texte non vide
            texts.append(text)
            offer_ids.append(offer['id'])
    
    logger.info(f"Textes préparés: {len(texts)}")
    
    return texts, offer_ids

def update_offers_with_embeddings(
    db, 
    offer_ids: List[str], 
    embeddings, 
    collection_name: str = "offres_unified"
):
    """
    Met à jour les offres dans MongoDB avec leurs embeddings.
    
    Args:
        db: Instance de base de données MongoDB
        offer_ids: Liste des IDs d'offres
        embeddings: Array numpy des embeddings
        collection_name: Nom de la collection MongoDB
    """
    collection = db[collection_name]
    updated = 0
    
    logger.info(f"Mise à jour de {len(offer_ids)} offres avec embeddings...")
    
    for offer_id, embedding in tqdm(
        zip(offer_ids, embeddings), 
        total=len(offer_ids),
        desc="Mise à jour MongoDB"
    ):
        result = collection.update_one(
            {"id": offer_id},
            {"$set": {"embedding": embedding.tolist()}}
        )
        if result.modified_count > 0:
            updated += 1
    
    logger.info(f"Offres mises à jour: {updated}/{len(offer_ids)}")

def generate_and_store_embeddings(
    db_name: str = "job_market",
    collection_name: str = "offres_unified",
    batch_size: int = 32
):
    """
    Pipeline complet de génération et stockage des embeddings.
    
    Args:
        db_name: Nom de la base de données MongoDB
        collection_name: Nom de la collection
        batch_size: Taille des batchs pour la génération
    """
    logger.info("=== GÉNÉRATION DES EMBEDDINGS ===")
    
    db = get_database(db_name)
    collection = db[collection_name]
    
    try:
        # 1. Chargement des offres sans embeddings
        logger.info(f"Chargement des offres depuis {collection_name}...")
        query = {"embedding": {"$exists": False}}
        offers = list(collection.find(query))
        
        if not offers:
            logger.info("Aucune offre à traiter (toutes ont déjà des embeddings)")
            return
        
        logger.info(f"Offres à traiter: {len(offers)}")
        
        # 2. Préparation des textes
        texts, offer_ids = prepare_texts_from_offers(offers)
        
        if not texts:
            logger.warning("Aucun texte valide à vectoriser")
            return
        
        # 3. Générer les embeddings
        embeddings = generate_embeddings(
            texts, 
            batch_size=batch_size,
            show_progress=True
        )
        
        # 4. Mise à jour MongoDB
        update_offers_with_embeddings(db, offer_ids, embeddings, collection_name)
        
        # 5. Statistiques finales
        total_with_embeddings = collection.count_documents({"embedding": {"$exists": True}})
        total_offers = collection.count_documents({})
        
        logger.info("\n=== STATISTIQUES FINALES ===")
        logger.info(f"Total offres: {total_offers}")
        logger.info(f"Avec embeddings: {total_with_embeddings}")
        logger.info(f"Sans embeddings: {total_offers - total_with_embeddings}")
        logger.info(f"Dimension embeddings: {get_embedding_dimension()}")
        
        logger.info("\n=== PIPELINE TERMINÉ ===")
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des embeddings: {e}", exc_info=True)
        raise
    finally:
        logger.info("Connexion MongoDB fermée")


if __name__ == "__main__":
    generate_and_store_embeddings()