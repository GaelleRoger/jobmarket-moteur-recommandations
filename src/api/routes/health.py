from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import Elasticsearch
from elasticsearch import ConnectionError as ESConnectionError
from ..dependencies import get_es_client
router = APIRouter(tags=["Health"])
@router.get("/health")
def health(es: Elasticsearch = Depends(get_es_client)) -> Dict[str, Any]:
    try:
        if not es.ping():
            raise HTTPException(status_code=503, detail="Elasticsearch unreachable")
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")
    return {"status": "ok"}