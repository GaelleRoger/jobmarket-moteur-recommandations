"""
Cosine : Applique la similarite cosinus entre les descriptions des offres d'emploi et une requete.
Retourne les offres les plus pertinentes.
Utilise Elasticsearch pour capturer les offres enrichies avec des embeddings.
"""
import sys
from pathlib import Path
src_path = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(src_path))

import logging
import numpy as np
from elasticsearch import ConnectionError as ESConnectionError
from sentence_transformers import SentenceTransformer
from src.esearch.connexion import connect_elasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_model = None

# Charger le modèle d'embedding globalement
def load_embedding_model(model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model

def get_offres_from_elasticsearch(index_name: str = "offres_unified", batch_size: int = 1000) -> list[dict]:
    """
    Récupère toutes les offres enrichies depuis Elasticsearch sous forme JSON.
    Utilise search_after pour paginer efficacement.
    
    :param index_name: Nom de l'index Elasticsearch (défaut: "offres_unified")
    :param batch_size: Nombre de documents à récupérer par batch (défaut: 1000)
    :return: Liste de documents JSON avec embeddings
    """
    try:
        es = connect_elasticsearch()
        logger.info(f"=== GET : Offres avec embeddings (Elasticsearch {index_name}) ===")
        
        # Vérifier que l'index existe
        if not es.indices.exists(index=index_name):
            logger.warning(f"Index {index_name} n'existe pas dans Elasticsearch")
            return []
        
        offres_list = []
        
        # Utiliser search_after pour paginer efficacement (recommandé)
        query = {
            "size": batch_size,
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "embedding"}}
                    ]
                }
            },
            "sort": [{"_id": "asc"}]  # Tri pour utiliser search_after
        }
        
        search_after = None
        
        while True:
            query['sort'] = [
                {'timestamp': {'order': 'desc'}},  # Tri par date (plus récent d'abord)
                {'id.keyword': {'order': 'asc'}}   # Tie-breaker pour garantir l'unicité
            ] 
            if search_after:
                query["search_after"] = search_after
            
            response = es.search(index=index_name, **query)
            hits = response.get("hits", {}).get("hits", [])
            
            if not hits:
                break
            
            for hit in hits:
                doc = hit["_source"]
                doc["_id"] = hit["_id"]  # Ajouter l'ID ES
                offres_list.append(doc)
            
            # Récupérer la dernière clé pour search_after
            search_after = hits[-1]["sort"]
        
        logger.info(f"{len(offres_list)} offres chargées d'Elasticsearch")
        return offres_list
        
    except ESConnectionError as e:
        logger.error(f"Erreur de connexion à Elasticsearch : {e}")
        return []
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents Elasticsearch : {e}")
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

    offres = get_offres_from_elasticsearch()
    logger.info(f"Nombre d'offres récupérées: {len(offres)}")
    
    logger.info(f"Requete test: {query['query']}")

    top_offres = rank_offres_by_similarity(offres, query_embedding, top_k=5)
    display_results(top_offres, show_description=True)
