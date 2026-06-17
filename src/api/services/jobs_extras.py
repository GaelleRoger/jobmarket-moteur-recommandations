# src/api/services/jobs_extras.py

from typing import Any, Dict, Optional
from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError

from src.api.config import ES_INDEX_OFFERS  # pour constance
# Indices de l'ancienne version (à confirmer/ajouter dans config)
ES_TENSION_INDEX = "tension_dept_ft_pro"
ES_EQPT_INDEX = "score_eqpt_dept_insee_pro"


def get_tension_and_equipment_scores(
    es: Elasticsearch,
    rome_code: Optional[str],
    codedep: Optional[str],
) -> Dict[str, Any]:
    """Récupère indicateur tension + scores équipements note_sur_5 par département."""
    tension_value: Optional[float] = None
    equipment_scores: Optional[Dict[str, int]] = None

    # ========== PARTIE 1 : TENSION (nécessite rome_code ET codedep) ==========
    if rome_code and codedep:
        tension_query: Dict[str, Any] = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"code_ROME.keyword": rome_code}},
                        {"term": {"type_territoire.keyword": "DEP"}},
                        {"term": {"code_territoire.keyword": codedep}},
                    ]
                }
            }
        }

        try:
            tension_resp = es.search(index=ES_TENSION_INDEX, body=tension_query)
        except ESConnectionError:
            tension_resp = {}
        except Exception:
            tension_resp = {}

        tension_hits = tension_resp.get("hits", {}).get("hits", [])
        if tension_hits:
            tension_value = tension_hits[0].get("_source", {}).get("valeurPrincipaleNombre")

    # ========== PARTIE 2 : ÉQUIPEMENTS (nécessite SEULEMENT codedep) ==========
    if codedep:
        eqpt_query: Dict[str, Any] = {
            "query": {"term": {"territory.keyword": codedep}}
        }

        try:
            eqpt_resp = es.search(index=ES_EQPT_INDEX, body=eqpt_query)
        except ESConnectionError:
            eqpt_resp = {}
        except Exception:
            eqpt_resp = {}

        eqpt_hits = eqpt_resp.get("hits", {}).get("hits", [])
        if eqpt_hits:
            eqpt_source = eqpt_hits[0].get("_source", {})
            services_raw = eqpt_source.get("services", {})
            equipment_scores = {
                "services_particuliers": int(services_raw.get("services_particuliers", {}).get("note_sur_5", 0)),
                "commerces": int(services_raw.get("commerces", {}).get("note_sur_5", 0)),
                "enseignement": int(services_raw.get("enseignement", {}).get("note_sur_5", 0)),
                "sante_action_sociale": int(services_raw.get("sante_action_sociale", {}).get("note_sur_5", 0)),
                "transports_deplacements": int(services_raw.get("transports_deplacements", {}).get("note_sur_5", 0)),
                "sports_loisirs_culture": int(services_raw.get("sports_loisirs_culture", {}).get("note_sur_5", 0)),
                "tourisme": int(services_raw.get("tourisme", {}).get("note_sur_5", 0)),
                "total": int(services_raw.get("total", {}).get("note_sur_5", 0)),
            }

    return {
        "tension_value": tension_value,
        "equipment_scores": equipment_scores,
    }