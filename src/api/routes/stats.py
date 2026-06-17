"""
Routes statistiques pour l'analyse descriptive des offres d'emploi.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from elasticsearch import Elasticsearch
from elasticsearch import ConnectionError as ESConnectionError
 
from src.api.config import ES_INDEX_OFFERS
from src.api.dependencies import get_es_client
from src.api.models.schemas import (
    TotalJobsResponse,
    DepartmentStat,
    JobsByDepartmentResponse,
    RegionStat,
    JobsByRegionResponse,
    CompetenceStat,
    TopCompetencesResponse
)
 
router = APIRouter(prefix="/api/v1/stats", tags=["Statistics"])
 
 
@router.get("/total", response_model=TotalJobsResponse)
def get_total_jobs(es: Elasticsearch = Depends(get_es_client)) -> TotalJobsResponse:
    """
    Retourne le nombre total d'offres d'emploi dans la base de données.
    """
    try:
        response = es.count(index=ES_INDEX_OFFERS)
        total = response.get("count", 0)
        
        return TotalJobsResponse(
            total=total,
            message=f"Nombre total d'offres d'emploi : {total}"
        )
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")
 
 
@router.get("/by_department", response_model=JobsByDepartmentResponse)
def get_jobs_by_department(
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de départements à retourner"),
    es: Elasticsearch = Depends(get_es_client)
) -> JobsByDepartmentResponse:
    """
    Retourne le nombre d'offres d'emploi par département.
    """
    query = {
        "size": 0,
        "aggs": {
            "departments": {
                "terms": {
                    "field": "lieuTravail.codeDep.keyword",
                    "size": limit,
                    "order": {"_count": "desc"}
                },
                "aggs": {
                    "lib_dep": {
                        "terms": {
                            "field": "lieuTravail.libDep.keyword",
                            "size": 1
                        }
                    }
                }
            }
        }
    }
 
    try:
        response = es.search(index=ES_INDEX_OFFERS, body=query)
        buckets = response.get("aggregations", {}).get("departments", {}).get("buckets", [])
        
        departments = []
        for bucket in buckets:
            code_dep = bucket.get("key")
            count = bucket.get("doc_count", 0)
            
            lib_dep_buckets = bucket.get("lib_dep", {}).get("buckets", [])
            lib_dep = lib_dep_buckets[0].get("key") if lib_dep_buckets else None
            
            departments.append(DepartmentStat(
                code_dep=code_dep,
                lib_dep=lib_dep,
                count=count
            ))
        
        return JobsByDepartmentResponse(
            departments=departments,
            total_departments=len(departments)
        )
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")
 
 
@router.get("/by_region", response_model=JobsByRegionResponse)
def get_jobs_by_region(
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de régions à retourner"),
    es: Elasticsearch = Depends(get_es_client)
) -> JobsByRegionResponse:
    """
    Retourne le nombre d'offres d'emploi par région.
    """
    query = {
        "size": 0,
        "aggs": {
            "regions": {
                "terms": {
                    "field": "lieuTravail.codeReg.keyword",
                    "size": limit,
                    "order": {"_count": "desc"}
                },
                "aggs": {
                    "lib_reg": {
                        "terms": {
                            "field": "lieuTravail.libReg.keyword",
                            "size": 1
                        }
                    }
                }
            }
        }
    }
 
    try:
        response = es.search(index=ES_INDEX_OFFERS, body=query)
        buckets = response.get("aggregations", {}).get("regions", {}).get("buckets", [])
        
        regions = []
        for bucket in buckets:
            code_reg = bucket.get("key")
            count = bucket.get("doc_count", 0)
            
            lib_reg_buckets = bucket.get("lib_reg", {}).get("buckets", [])
            lib_reg = lib_reg_buckets[0].get("key") if lib_reg_buckets else None
            
            regions.append(RegionStat(
                code_reg=code_reg,
                lib_reg=lib_reg,
                count=count
            ))
        
        return JobsByRegionResponse(
            regions=regions,
            total_regions=len(regions)
        )
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")
 
 
@router.get("/top_competences", response_model=TopCompetencesResponse)
def get_top_competences(
    limit: int = Query(50, ge=1, le=500, description="Nombre de compétences à retourner"),
    es: Elasticsearch = Depends(get_es_client)
) -> TopCompetencesResponse:
    """
    Retourne les compétences les plus demandées dans les offres d'emploi.
    
    Note: Le champ 'competences' est peu rempli dans les données, 
    les résultats peuvent être limités.
    """
    query = {
        "size": 0,
        "aggs": {
            "competences": {
                "terms": {
                    "field": "competences.libelle.keyword",
                    "size": limit,
                    "order": {"_count": "desc"}
                }
            }
        }
    }
 
    try:
        response = es.search(index=ES_INDEX_OFFERS, body=query)
        buckets = response.get("aggregations", {}).get("competences", {}).get("buckets", [])
        
        competences = []
        for bucket in buckets:
            libelle = bucket.get("key")
            count = bucket.get("doc_count", 0)
            
            competences.append(CompetenceStat(
                libelle=libelle,
                count=count
            ))
        
        return TopCompetencesResponse(
            competences=competences,
            total_unique_competences=len(competences)
        )
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")