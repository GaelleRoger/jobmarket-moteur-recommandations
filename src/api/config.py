import os
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX_OFFERS = os.getenv("ES_INDEX_OFFERS", "offres_unified")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
DEFAULT_DESCRIPTION_MAX_CHARS = int(os.getenv("DESCRIPTION_MAX_CHARS", "2000"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
DEFAULT_CANDIDATE_POOL = int(os.getenv("DEFAULT_CANDIDATE_POOL", "200"))
MAX_CANDIDATE_POOL = int(os.getenv("MAX_CANDIDATE_POOL", "500"))