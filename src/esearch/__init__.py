"""
Module Esearch.
"""
from .config import ESEARCH_CONFIG
from .connexion import connect_elasticsearch, create_index_mapping
__all__ = [
    'ESEARCH_CONFIG'
    'connect_elasticsearch',
    'create_index_mapping'
]
