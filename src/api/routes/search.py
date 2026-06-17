"""
Routes de recherche sémantique d'offres d'emploi.
Utilise le modèle maison pour calculer la similarité cosinus après filtrage géographique.
Le filtre géographique est OBLIGATOIRE (commune, département ou région).
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import Elasticsearch
import numpy as np

from src.api.config import DEFAULT_DESCRIPTION_MAX_CHARS
from src.api.dependencies import get_es_client
from src.api.models.schemas import GeoFilter, SemanticSearchRequest, SemanticSearchResponse
from src.api.services.embeddings import embed_text
from src.api.services.elasticsearch import geo_fallback_scopes, get_offers_by_geo
from src.api.services.similarity import cosine_similarity, normalize_vector
from src.api.services.jobs_extras import get_tension_and_equipment_scores
from src.api.models.schemas import SemanticSearchResponseExtended, SemanticSearchHitExtended 

router = APIRouter(prefix="/api/v1", tags=["Search"])

def _truncate_description(job: Dict[str, Any], max_chars: int) -> Dict[str, Any]:
    """Tronque la description d'une offre."""
    desc = job.get("description")
    if isinstance(desc, str) and len(desc) > max_chars:
        job["description"] = desc[:max_chars] + "..."
    return job

def _remove_embedding(job: Dict[str, Any]) -> Dict[str, Any]:
    """Supprime l'embedding d'une offre."""
    job.pop("embedding", None)
    return job

def _calculate_cosine_scores(
    query_vec: np.ndarray,
    offers: List[Dict[str, Any]],
    top_k: int
) -> List[tuple[float, Dict[str, Any]]]:
    """
    Calcule les scores de similarité cosinus entre la requête et les offres.
    
    Args:
        query_vec: Vecteur de la requête (normalisé)
        offers: Liste des offres avec embeddings
        top_k: Nombre de résultats à retourner
        
    Returns:
        Liste de (score, offre) triée par score décroissant
    """
    scored_items = []
    
    for offer in offers:
        embedding = offer.get("embedding")
        if not embedding:
            continue
        
        doc_vec = np.array(embedding, dtype=np.float32)
        doc_vec = normalize_vector(doc_vec)
        
        score = cosine_similarity(query_vec, doc_vec)
        scored_items.append((float(score), offer))
    
    # Trier par score décroissant et limiter à top_k
    scored_items.sort(key=lambda x: x[0], reverse=True)
    return scored_items[:top_k]

@router.post("/search/semantic", response_model=SemanticSearchResponseExtended)  
def search_semantic(
    payload: SemanticSearchRequest,
    es: Elasticsearch = Depends(get_es_client),
) -> SemanticSearchResponseExtended:
    """
    Recherche sémantique d'offres d'emploi avec filtre géographique OBLIGATOIRE.
    
    Architecture:
    1. Filtre géographique (commune/département/région) avec fallback automatique
    2. Récupération de TOUTES les offres du territoire filtré
    3. Génération de l'embedding de la requête
    4. Calcul de la similarité cosinus en Python (modèle maison)
    5. Tri et retour des top K résultats
    
    Note: Le filtre géographique est obligatoire. Pas de niveau national.
    """
    # Vérifier que le filtre geo est fourni
    if not payload.geo:
        raise HTTPException(
            status_code=422, 
            detail="Le filtre géographique est obligatoire (commune, département ou région)"
        )
    
    # 1) Embedding requête (normalisé)
    query_vec = embed_text(payload.text)
    query_vec = normalize_vector(query_vec)
        
    # 2) Construire les scopes geo (fallback) ou strict
    if payload.geo_strategy == "strict":
        scopes = [("strict", payload.geo)]
    else:
        scopes = geo_fallback_scopes(payload.geo)

    if not scopes:
        raise HTTPException(
            status_code=422,
            detail="Filtre géographique invalide : impossible de construire des scopes de recherche"
        )

    selected_level = None
    selected_geo: Dict[str, Any] = {}
    selected_offers: List[Dict[str, Any]] = []

    # 3) Récupération des offres avec fallback jusqu'à obtenir >= top_k offres
    for level, geo_scope in scopes:
        if not geo_scope:
            continue
            
        offers = get_offers_by_geo(es=es, geo=geo_scope)
        
        # Si on a assez d'offres, on s'arrête
        if len(offers) >= payload.top_k:
            selected_level = level
            selected_offers = offers
            selected_geo = {
                "region_code": geo_scope.region_code,
                "departement_code": geo_scope.departement_code,
                "commune_code": geo_scope.commune_code,
            }
            selected_geo = {k: v for k, v in selected_geo.items() if v is not None}
            break
    
    # Si on n'a pas trouvé assez de résultats, prendre le dernier scope (région)
    if not selected_level and scopes:
        level, geo_scope = scopes[-1]
        if geo_scope:
            selected_level = level
            selected_offers = get_offers_by_geo(es=es, geo=geo_scope)
            selected_geo = {
                "region_code": geo_scope.region_code,
                "departement_code": geo_scope.departement_code,
                "commune_code": geo_scope.commune_code,
            }
            selected_geo = {k: v for k, v in selected_geo.items() if v is not None}
    
    # Si toujours aucun résultat
    if not selected_offers:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune offre trouvée pour le filtre géographique demandé. Essayez un autre département ou une région."
        )

    # 4) Calcul cosinus "maison" sur toutes les offres filtrées
    rescored = _calculate_cosine_scores(query_vec, selected_offers, payload.top_k)

    # 5) Formater la réponse (sans embedding, description tronquée)
    items: List[Dict[str, Any]] = []
    for score, job in rescored:
        job_dict = dict(job)
        job_dict = _remove_embedding(job_dict)
        job_dict = _truncate_description(job_dict, DEFAULT_DESCRIPTION_MAX_CHARS)
    

        # Extraction pour extras
        rome_code = job_dict.get("romeCode")
        lieu_travail = job_dict.get("lieuTravail") or {}
        codedep = lieu_travail.get("codeDep")

        extras = get_tension_and_equipment_scores(es, rome_code=rome_code, codedep=codedep)

        items.append({
            "similarity_score": score,
            "job": job_dict,
            "tension_value": extras["tension_value"],
            "equipment_scores": extras["equipment_scores"],
        })

    return SemanticSearchResponseExtended(
        items=items,
        top_k=payload.top_k,
        candidate_pool=len(selected_offers),
        score_type="cosine-dot-normalized",  # comme dans ton schéma
        geo_strategy=payload.geo_strategy,
        geo_applied_level=selected_level or "unknown",
        geo_applied=selected_geo,
    )