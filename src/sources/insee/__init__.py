"""
Module INSEE
"""
from .fetch_pop_eqpt import fetch_population, fetch_equipements,fetch_eqpt_metadata
__all__ = [
    'fetch_population',
    'fetch_equipements',
    'fetch_eqpt_metadata'
]