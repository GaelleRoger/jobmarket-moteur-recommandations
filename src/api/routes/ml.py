"""
Routes ML pour les calculs de similarité et analyses textuelles.
"""
from typing import List
import time
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from elasticsearch import Elasticsearch
from elasticsearch import ConnectionError as ESConnectionError
from sentence_transformers import SentenceTransformer
import heapq


from src.api.config import ES_INDEX_OFFERS, EMBEDDING_MODEL_NAME
from src.api.dependencies import get_es_client
from src.api.models.schemas import (CosineSimRequest, 
                                    JobInfo,
                                    ResultItem,
                                    StatsInfo,
                                    FinalComparisonResponse)

_model = None

# Charger le modèle d'embedding globalement
def load_embedding_model(model_name=EMBEDDING_MODEL_NAME):
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model

# Crée un embedding à partir d'une requête texte.
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
        "model": EMBEDDING_MODEL_NAME,
        "embedding_dimension": len(embedding),
        "embedding": embedding.tolist()  # conversion pour JSON
    }

# Calcul de la similarité cosinus. Les vecteurs sont deja normalisés.
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcul de la similarité cosinus. Les vecteurs sont deja normalisés.
    """
    return (np.dot(vec1, vec2)+1)/2  # Normalisé entre 0 et 1

# ========== FONCTION 1 : CALCUL MANUEL ==========

def _calculate_similarity_manual(
    query_emb: np.ndarray,
    es: Elasticsearch,
    top_k: int,
    max_docs: int = 5000,
    timeout_s: float = 8.0
) -> tuple[list[dict], float]:
    """
    Calcul manuel SAFE :
    - limite documents
    - streaming
    - RAM bornée
    """
    start_time = time.time()

    batch_size = 500
    processed_docs = 0
    search_after = None

    # min-heap pour garder les top_k
    heap = []

    while True:
        if processed_docs >= max_docs:
            break
        if time.time() - start_time > timeout_s:
            break

        body = {
            "size": batch_size,
            "query": {
                "bool": {
                    "must": [{"exists": {"field": "embedding"}}]
                }
            },
            "sort": [
                {"timestamp": "desc"},
                {"id.keyword": "asc"}
            ]
        }

        if search_after:
            body["search_after"] = search_after

        resp = es.search(index=ES_INDEX_OFFERS, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            break

        for hit in hits:
            if processed_docs >= max_docs:
                break

            doc = hit["_source"]
            emb = doc.get("embedding")
            if emb is None:
                continue

            score = cosine_similarity(query_emb, emb)

            item = {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "employer": doc.get("employer"),
                "location": doc.get("location"),
                "description": doc.get("description", "")[:250],
                "score": float(score),
            }

            if len(heap) < top_k:
                heapq.heappush(heap, (score, item))
            else:
                heapq.heappushpop(heap, (score, item))

            processed_docs += 1

        search_after = hits[-1]["sort"]

    # Trier final décroissant
    top_items = [x[1] for x in sorted(heap, reverse=True)]

    exec_ms = (time.time() - start_time) * 1000
    return top_items, exec_ms


# ========== FONCTION 2 : CALCUL NATIF ELASTICSEARCH ==========

def _calculate_similarity_native(
    query_emb: list,
    es: Elasticsearch,
    top_k: int
) -> tuple[List[dict], float, int]:
    """
    Calcule la similarité cosinus en utilisant la recherche KNN NATIVE d'Elasticsearch.
    
    Returns:
        tuple: (résultats triés, temps d'exécution en ms)
    """
    start_time = time.time()
    
    # Construction et exécution de la recherche KNN
    resp = es.search(
        index=ES_INDEX_OFFERS,
        body={
            "knn": {
                "field": "embedding",
                "query_vector": query_emb,
                "k": top_k,
                "num_candidates": top_k * 3
            },
            "query": {
                "match_all": {}
            },
            "_source": ["id", "title", "description", "employer", "location"]
        }
    )

    hits = resp.get("hits", {}).get("hits", [])

    scored_items = []
    for hit in hits:
        doc = hit["_source"]
        es_score = hit["_score"]-1
        
        scored_items.append({
            "id": doc.get("id"),
            "title": doc.get("title"),
            "employer": doc.get("employer"),
            "location": doc.get("location"),
            "description": doc.get("description","")[:250],
            "score": float(es_score)
        })

    execution_time_ms = (time.time() - start_time) * 1000
    
    return scored_items, execution_time_ms

# ========== ROUTE API ==========
router = APIRouter(prefix="/api/v1/ml", tags=["ML"])

@router.post("/similarity/cosine/compare", response_model=FinalComparisonResponse)
async def compare_similarity_calculations(
    payload: CosineSimRequest,
    es: Elasticsearch = Depends(get_es_client),
) -> FinalComparisonResponse:
    """
    Compare les calculs de similarité cosinus entre la méthode MANUELLE et NATIVE Elasticsearch.
    
    Retourne les résultats des deux méthodes entrelacés par rang :
    - Rang 1 manuel, Rang 1 natif
    - Rang 2 manuel, Rang 2 natif
    - etc.
    """
    try:
        # Générer l'embedding une seule fois
        query_vec = create_embedding(payload.text)
        query_emb_list = query_vec["embedding"]
        query_emb_array = np.array(query_emb_list)

        # EXÉCUTER LES DEUX MÉTHODES
        manual_results, manual_time = await run_in_threadpool(
            _calculate_similarity_manual,
            query_emb_array, es, payload.top_k
        )
        
        native_results, native_time = await run_in_threadpool(
            _calculate_similarity_native,
            query_emb_list, es, payload.top_k
        )

        # DEBUG : Afficher les résultats
        print(f"DEBUG - Manual results count: {len(manual_results)}")
        print(f"DEBUG - Native results count: {len(native_results)}")
        
        if manual_results:
            print(f"DEBUG - First manual result: {manual_results[0]}")
        if native_results:
            print(f"DEBUG - First native result: {native_results[0]}")

        # CONSTRUIRE LA LISTE D'ITEMS ENTRELACÉS
        items = []
        
        max_results = min(len(manual_results), len(native_results), payload.top_k)
        print(f"DEBUG - Processing {max_results} results")

        for rank in range(max_results):
            manual_item = manual_results[rank]
            native_item = native_results[rank]
            
            # Item MANUEL
            items.append(
                ResultItem(
                    method="manual",
                    rank=rank + 1,
                    similarity_score=manual_item["score"],
                    job=JobInfo(
                        id=manual_item["id"],
                        title=manual_item["title"],
                        employer=manual_item["employer"],
                        location=manual_item["location"],
                        description=manual_item["description"]
                    )
                )
            )
            
            # Item NATIVE
            items.append(
                ResultItem(
                    method="native",
                    rank=rank + 1,
                    similarity_score=native_item["score"],
                    job=JobInfo(
                        id=native_item["id"],
                        title=native_item["title"],
                        employer=native_item["employer"],
                        location=native_item["location"],
                        description=native_item["description"]
                    )
                )
            )
        
        # CONSTRUIRE LES STATS
        same_top_1 = (
            manual_results[0]["id"] == native_results[0]["id"] 
            if manual_results and native_results else False
        )
        
        stats = StatsInfo(
            execution_time_ms_manual=round(manual_time, 2),
            execution_time_ms_native=round(native_time, 2),
            native_is_faster=native_time < manual_time,
            same_top_1=same_top_1
        )

        print(f"DEBUG - Final items count: {len(items)}")

        return FinalComparisonResponse(
            items=items,
            stats=stats,
            top_k=payload.top_k,
            input_text=payload.text,
            model_name=EMBEDDING_MODEL_NAME
        )

    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")