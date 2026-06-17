"""
Module France Travail.
"""
from .auth import get_access_token, FT_SCOPE_OFFRES, FT_SCOPE_STATS, FT_SCOPE_REFERENTIEL
from .fetch_offers import fetch_offers
from .fetch_rome_stats import fetch_territory, fetch_rome_codes,fetch_tension_indicator

__all__ = [
    'get_access_token',
    'FT_SCOPE_OFFRES',
    'FT_SCOPE_STATS',
    'FT_SCOPE_REFERENTIEL',
    'fetch_offers',
    'fetch_territory',
    'fetch_rome_codes',
    'fetch_tension_indicator'
]
