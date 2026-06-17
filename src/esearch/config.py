"""
Configuration Elasticsearch
"""
import os
from dotenv import load_dotenv
load_dotenv()
ESEARCH_CONFIG = {
    "host": os.getenv("ESEARCH_HOST", "elasticsearch"),
    "port": int(os.getenv("ESEARCH_PORT", 9200)),
    "user": os.getenv("ESEARCH_USER", "elastic"),
    "password": os.getenv("ESEARCH_PASSWORD", None),
    "use_ssl": os.getenv("ESEARCH_USE_SSL", "false").lower() == "true",
    "verify_certs": os.getenv("ESEARCH_VERIFY_CERTS", "false").lower() == "true"
}