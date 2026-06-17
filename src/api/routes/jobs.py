from typing import Any, Dict,List

from fastapi import APIRouter, Depends, HTTPException, Query
from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError

from src.api.dependencies import get_es_client
from src.api.models.schemas import Job, PaginatedJobs
from src.api.services.elasticsearch import get_job_by_business_id
from src.api.config import ES_INDEX_OFFERS

router = APIRouter(prefix="/api/v1", tags=["Jobs"])


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str, es: Elasticsearch = Depends(get_es_client)) -> Job:
    job = get_job_by_business_id(es, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # On ne renvoie jamais l'embedding
    job.pop("embedding", None)
    return job

@router.get("/job_dept/", response_model=PaginatedJobs)
def jobs_by_department(
    codedep: str = Query(..., alias="codedep", description="Code département, ex 75"),
    limit: int = Query(10, ge=1, le=100, description="Nombre max d'offres à retourner"),
    offset: int = Query(0, ge=0, description="Nombre d'offres à ignorer pour la pagination"),
    es: Elasticsearch = Depends(get_es_client),
) -> PaginatedJobs:
    """
    Retourne les offres pour un département donné avec pagination.
    """
    query: Dict[str, Any] = {
        "query": {"term": {"lieuTravail.codeDep.keyword": codedep}},
        "from": offset,
        "size": limit,
    }

    try:
        response = es.search(index=ES_INDEX_OFFERS, body=query)
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")

    hits: Dict[str, Any] = response.get("hits", {})
    total: int = hits.get("total", {}).get("value", 0)
    items: List[Dict[str, Any]] = [hit.get("_source", {}) for hit in hits.get("hits", [])]

    return PaginatedJobs(items=items, total=total, limit=limit, offset=offset)