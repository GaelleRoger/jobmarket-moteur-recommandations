from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

class GeoFilter(BaseModel):
    region_code: Optional[str] = None
    departement_code: Optional[str] = None
    commune_code: Optional[str] = None

class SemanticSearchRequest(BaseModel):
    text: str = Field(..., min_length=1)
    top_k: int = Field(10, ge=1, le=50)
    candidate_pool: int = Field(200, ge=10, le=500)
    geo: Optional[GeoFilter] = None
    geo_strategy: str = Field("fallback", pattern="^(fallback|strict)$")

class JobLieuTravail(BaseModel):
    codeReg: Optional[str] = None
    libReg: Optional[str] = None
    codeDep: Optional[str] = None
    libDep: Optional[str] = None
    codeCom: Optional[str] = None
    libCom: Optional[str] = None
    codePostal: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    libelleOriginal: Optional[str] = None
    typeGeo: Optional[str] = None

class Job(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    employer: Optional[str] = None
    location: Optional[str] = None
    lieuTravail: Optional[JobLieuTravail] = None
    posted_at: Optional[str] = None
    source: Optional[str] = None
    apply_link: Optional[str] = None
    romeCode: Optional[str] = None
    description: Optional[str] = None

class PaginatedJobs(BaseModel):
    items: List[Job]
    total: int
    limit: int
    offset: int

class SemanticSearchHit(BaseModel):
    similarity_score: float
    job: Job

class SemanticSearchResponse(BaseModel):
    items: List[SemanticSearchHit]
    top_k: int
    candidate_pool: int
    score_type: str = "cosine_dot_normalized"
    geo_strategy: str
    geo_applied_level: str
    geo_applied: Dict[str, Any]

# schemas.py (ajoute après SemanticSearchResponse)

class EquipmentScores(BaseModel):
    """Scores équipements note_sur_5 du département."""
    servicesparticuliers: Optional[int] = None
    commerces: Optional[int] = None
    enseignement: Optional[int] = None
    santeactionsociale: Optional[int] = None
    transportsdeplacements: Optional[int] = None
    sportsloisirsculture: Optional[int] = None
    tourisme: Optional[int] = None
    total: Optional[int] = None


class SemanticSearchHitExtended(BaseModel):
    """Item enrichi avec tension et équipements."""
    similarity_score: float
    job: Job
    tension_value: Optional[float] = Field(None, description="Indicateur de tension ROME/département")
    equipment_scores: Optional[EquipmentScores] = Field(
        None, description="Scores équipements note_sur_5 du département"
    )


class SemanticSearchResponseExtended(SemanticSearchResponse):
    """Réponse sémantique enrichie."""
    items: List[SemanticSearchHitExtended]  # Remplace List[SemanticSearchHit]

    
# ============== MODÈLES POUR LES STATISTIQUES ==============
 
class TotalJobsResponse(BaseModel):
    total: int
    message: str
 
 
class DepartmentStat(BaseModel):
    code_dep: str
    lib_dep: Optional[str] = None
    count: int
 
 
class JobsByDepartmentResponse(BaseModel):
    departments: List[DepartmentStat]
    total_departments: int
 
 
class RegionStat(BaseModel):
    code_reg: str
    lib_reg: Optional[str] = None
    count: int
 
 
class JobsByRegionResponse(BaseModel):
    regions: List[RegionStat]
    total_regions: int
 
 
class CompetenceStat(BaseModel):
    libelle: str
    count: int
 
class TopCompetencesResponse(BaseModel):
    competences: List[CompetenceStat]
    total_unique_competences: int

# ============== MODÈLES POUR ML / SIMILARITÉ ==============

class CosineSimRequest(BaseModel):
    """Schéma de requête pour le calcul de similarité cosinus."""
    text: str = Field(..., min_length=1, description="Texte à analyser pour la similarité")
    top_k: int = Field(10, ge=1, le=100, description="Nombre de résultats similaires à retourner")

class JobInfo(BaseModel):
    """Informations d'une offre d'emploi"""
    id: str
    title: str
    employer: str | None = None
    location: str | None = None
    description: str

class ResultItem(BaseModel):
    """Un résultat avec méthode, rang, score et job"""
    method: Literal["manual", "native"]
    rank: int
    similarity_score: float
    job: JobInfo

    class Config:
        json_encoders = {
            float: lambda v: round(v, 5)
        }
        
class StatsInfo(BaseModel):
    """Statistiques consolidées"""
    calculation_mode_manual: str = "manual"
    execution_time_ms_manual: float
    calculation_mode_native: str = "native"
    execution_time_ms_native: float
    native_is_faster: bool
    same_top_1: bool

class FinalComparisonResponse(BaseModel):
    """Réponse finale avec le format souhaité"""
    items: List[ResultItem]
    stats: StatsInfo
    top_k: int
    input_text: str
    model_name: str
    class Config:
        protected_namespaces = ()  # autorise model_*
        json_encoders = {float: lambda v: round(v, 5)}  # si tu l'as déjà


class EquipmentScores(BaseModel):
    services_particuliers: Optional[int] = None
    commerces: Optional[int] = None
    enseignement: Optional[int] = None
    sante_action_sociale: Optional[int] = None
    transports_deplacements: Optional[int] = None
    sports_loisirs_culture: Optional[int] = None
    tourisme: Optional[int] = None
    total: Optional[int] = None

class SemanticSearchHitExtended(BaseModel):
    similarity_score: float
    job: Job
    tension_value: Optional[float] = None
    equipment_scores: Optional[EquipmentScores] = None

class SemanticSearchResponseExtended(SemanticSearchResponse):
    items: List[SemanticSearchHitExtended]  # override pour le nouveau type

