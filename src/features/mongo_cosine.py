"""
Cosine : Applique la similarite cosinus entre les descriptions des offres d'emploi et une requete.
Retourne les offres les plus pertinentes.
Utilise MongoDB pour capturer les offres enrichies avec des embeddings.
"""
import sys
from pathlib import Path
src_path = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(src_path))

import logging
import numpy as np
from pymongo.errors import PyMongoError
from sentence_transformers import SentenceTransformer
from src.mongodb import check_mongodb_connection, check_collection_exist
from src.utils import load_json, DATA_PRO_UNIFIED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_model = None

# Charger le modèle d'embedding globalement
def load_embedding_model(model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model

def get_offres_from_file(file_name: str ) -> list[dict]:
    """
    Récupère toutes les offres enrichies depuis fichier offres_unbified_with_embeddings sous forme JSON.

    :param file_name: Nom du fichier JSON contenant les offres enrichies
    :return: Liste de documents JSON avec embeddings
    """
    file_path = DATA_PRO_UNIFIED / file_name
    return load_json(file_path)

def get_offres_enrichies(db_name: str = "job_market") -> list[dict]:
    """
    Récupère toutes les offres enrichies depuis MongoDB sous forme JSON.
    
    :param db_name: Nom de la base MongoDB
    :return: Liste de documents JSON avec embeddings
    """
    db = check_mongodb_connection(db_name)
    if not check_collection_exist(db, "offres_unified"):
        return []

    try:
        collection = db["offres_unified"]
<<<<<<< HEAD
        logger.info("=== GET : Offres avec embeddings ===")
=======
        logger.info("=== GET : Offres avec embeddings (MongoDB) ===")
>>>>>>> origin/main
        offres_list = []
        for doc in collection.find():
            doc["_id"] = str(doc["_id"])  # MongoDB ObjectId n'est pas JSON serializable
            offres_list.append(doc)
<<<<<<< HEAD
        logger.info(f"{len(offres_list)} offres chargées")
        return offres_list
    except PyMongoError as e:
        logger.error(f"Erreur lors de la récupération des documents : {e}")
=======
        logger.info(f"{len(offres_list)} offres chargées de MongoDB")
        return offres_list
    except PyMongoError as e:
        logger.error(f"Erreur lors de la récupération des documents MongoDB : {e}")
>>>>>>> origin/main
        return []

def create_embedding(query: str) -> dict:
    """
    Crée un embedding à partir d'une requête texte.

    :param query: Texte à encoder
    :return: JSON avec la requête et son embedding
    """
    _model = load_embedding_model()
    embedding = _model.encode(query, normalize_embeddings=True)

    return {
        "query": query,
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "embedding_dimension": len(embedding),
        "embedding": embedding.tolist()  # conversion pour JSON
    }

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcul de la similarité cosinus. Les vecteurs sont deja normalisés.
    """
    return np.dot(vec1, vec2)

def rank_offres_by_similarity(offres: list[dict], query_embedding: list[float], top_k: int = 10) -> list[dict]:
    """
    Classe les offres par similarité cosinus avec la requête.
    """
    scored_offres = []

    for offre in offres:
        embedding = offre.get("embedding")
        if embedding is None:
            continue

        score = cosine_similarity(query_embedding, embedding)

        scored_offres.append({
            **offre,
            "similarity_score": score
        })

    # Tri décroissant (plus proche en premier)
    scored_offres.sort(key=lambda x: x["similarity_score"], reverse=True)

    return scored_offres[:top_k]

def display_results(results: list[dict], show_description: bool = True):
    """
    Affiche les résultats de manière formatée.
    
    :param results: Liste des offres avec scores de similarité
    :param show_description: Afficher ou non la description complète
    """
    if not results:
        print("Aucun résultat trouvé")
        return
        
    print(f"\n{'='*100}")
    print(f"Trouvé {len(results)} offres\n")
    
    for i, offre in enumerate(results, 1):
        score = offre.get('similarity_score', 0)
        
        print(f"{i}. SCORE DE SIMILARITÉ: {score:.4f}")
        print(f"Titre: {offre.get('title', 'N/A')}")
        print(f"Entreprise: {offre.get('employer', 'N/A')}")
        print(f"Lieu: {offre.get('location', 'N/A')}")
        
        if offre.get('lieuTravail'):
            lieu = offre['lieuTravail']
            print(f"      → Région: {lieu.get('libReg', 'N/A')}, "
                  f"Département: {lieu.get('libDep', 'N/A')}, "
                  f"Code Postal: {lieu.get('codePostal', 'N/A')}")
        
        if offre.get('posted_at'):
            print(f"Publié le: {offre['posted_at']}")
        
        if offre.get('source'):
            print(f"Source: {offre['source']}")

        if offre.get('apply_link'):
            print(f"Postuler: {offre['apply_link']}")
        
        if show_description and offre.get('description'):
            desc = offre['description']
            # Tronquer à 250 caractères
            desc_short = desc[:250] + "..." if len(desc) > 250 else desc
            print(f"Description: {desc_short}")
        
        print(f"   {'─'*96}\n")

if __name__ == "__main__":
    query = create_embedding("Data engineer spécialisé Docker, Snowflake et Kubernetes")
    query_embedding = query["embedding"]
    logger.info(f"Embedding de la requête créé avec dimension: {query['embedding_dimension']}")

<<<<<<< HEAD
    #data = get_offres_from_file("offres_unified_with_embeddings_20260108_143357.json")
=======
>>>>>>> origin/main
    offres = get_offres_enrichies()
    logger.info(f"Nombre d'offres récupérées: {len(offres)}")
    
    logger.info(f"Requete test: {query['query']}")

    top_offres = rank_offres_by_similarity(offres, query_embedding, top_k=5)
    display_results(top_offres, show_description=True)
