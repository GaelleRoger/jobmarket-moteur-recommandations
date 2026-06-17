"""
Services Elasticsearch pour la recherche d'offres d'emploi.
Gère les filtres géographiques, la récupération d'offres et le fallback géographique.
"""
from typing import Any, Dict, List, Optional, Tuple

from elasticsearch import Elasticsearch
from elasticsearch import ConnectionError as ESConnectionError

from src.api.config import ES_INDEX_OFFERS
from src.api.models.schemas import GeoFilter
from src.api.services.geo_mapping import get_region_from_department


def build_geo_filters(geo: GeoFilter) -> List[Dict[str, Any]]:
    """
    Construit les filtres Elasticsearch pour la géolocalisation.
    Utilise UNIQUEMENT le filtre le plus spécifique disponible.
    """
    filters: List[Dict[str, Any]] = []

    # Priorité : commune > département > région
    if geo.commune_code:
        filters.append({"term": {"lieuTravail.codeCom.keyword": geo.commune_code}})
    elif geo.departement_code:
        filters.append({"term": {"lieuTravail.codeDep.keyword": geo.departement_code}})
    elif geo.region_code:
        filters.append({"term": {"lieuTravail.codeReg.keyword": geo.region_code}})

    return filters


def geo_fallback_scopes(geo: Optional[GeoFilter]) -> List[Tuple[str, Optional[GeoFilter]]]:
    """
    Retourne une liste de (niveau, geo_effectif) à tester, du plus strict au plus large.
    Fallback: commune → département → région (pas de niveau national).
    """
    if not geo:
        return []  # Pas de filtre géo = pas de résultats

    scopes: List[Tuple[str, Optional[GeoFilter]]] = []

    # Dériver département depuis commune si non fourni
    dept = geo.departement_code
    if not dept and geo.commune_code and len(geo.commune_code) >= 2:
        # Cas DOM-TOM (971, 972, 973, 974, 976)
        if len(geo.commune_code) >= 3 and geo.commune_code[:3] in ("971", "972", "973", "974", "976"):
            dept = geo.commune_code[:3]
        else:
            dept = geo.commune_code[:2]

    # Dériver région depuis département si non fournie
    region = geo.region_code
    if not region and dept:
        region = get_region_from_department(dept)

    # 1) commune uniquement
    if geo.commune_code:
        scopes.append(("commune", GeoFilter(
            region_code=None,
            departement_code=None,
            commune_code=geo.commune_code,
        )))

    # 2) department uniquement
    if dept:
        scopes.append(("department", GeoFilter(
            region_code=None,
            departement_code=dept,
            commune_code=None,
        )))

    # 3) region uniquement (niveau le plus large)
    if region:
        scopes.append(("region", GeoFilter(
            region_code=region,
            departement_code=None,
            commune_code=None,
        )))

    # Dédoublonnage basique
    seen = set()
    unique_scopes: List[Tuple[str, Optional[GeoFilter]]] = []
    for level, g in scopes:
        key = (level, None if g is None else (g.region_code, g.departement_code, g.commune_code))
        if key in seen:
            continue
        seen.add(key)
        unique_scopes.append((level, g))

    return unique_scopes


def get_offers_by_geo(
    es: Elasticsearch,
    geo: Optional[GeoFilter],
    max_results: int = 10000
) -> List[Dict[str, Any]]:
    """
    Récupère TOUTES les offres filtrées géographiquement.
    Utilisé pour le calcul cosinus manuel en Python.
    
    Args:
        es: Client Elasticsearch
        geo: Filtre géographique (commune, département, région) - OBLIGATOIRE
        max_results: Nombre maximum d'offres à récupérer
        
    Returns:
        Liste des offres avec leurs embeddings
    """
    if not geo:
        return []  # Pas de filtre géo = pas de résultats
    
    query: Dict[str, Any] = {
        "bool": {
            "must": [
                {"exists": {"field": "embedding"}}
            ]
        }
    }
    
    # Ajouter les filtres géographiques
    geo_filters = build_geo_filters(geo)
    if geo_filters:
        query["bool"]["filter"] = geo_filters
    else:
        return []  # Pas de filtre valide = pas de résultats
    
    body = {
        "size": max_results,
        "query": query,
        "_source": {
            "includes": ["id", "title", "description", "employer", "location", "lieuTravail", "embedding", "posted_at", "source", "apply_link", "romeCode"],
            "excludes": []
        }
    }
    
    try:
        resp = es.search(index=ES_INDEX_OFFERS, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        return [hit["_source"] for hit in hits]
    except ESConnectionError as e:
        raise RuntimeError(f"Elasticsearch connection error: {e}") from e


def get_job_by_business_id(es: Elasticsearch, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Cherche une offre via le champ métier id (id.keyword).
    """
    query = {
        "size": 1,
        "query": {"term": {"id.keyword": job_id}},
    }

    resp = es.search(index=ES_INDEX_OFFERS, body=query)
    hits = (resp.get("hits") or {}).get("hits") or []
    if not hits:
        return None
    return hits[0].get("_source") or {}