from elasticsearch import Elasticsearch
from .config import ES_HOST
def get_es_client() -> Elasticsearch:
    return Elasticsearch([ES_HOST])