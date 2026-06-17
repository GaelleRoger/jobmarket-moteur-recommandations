from sentence_transformers import SentenceTransformer
import numpy as np
from src.api.config import EMBEDDING_MODEL_NAME

_model = None
def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model

def embed_text(text: str) -> np.ndarray:
    """
    Retourne un vecteur numpy float32 normalisé (norme L2=1).
    """
    model = get_embedding_model()
    vec = model.encode(text, normalize_embeddings=True)
    return np.asarray(vec, dtype=np.float32)