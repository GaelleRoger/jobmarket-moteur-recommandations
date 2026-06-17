"""
Module de génération d'embeddings pour les textes.
Utilise Sentence Transformers pour créer des représentations vectorielles.
"""
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Variable globale pour le modèle
_model = None

def load_embedding_model(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    """
    Charge le modèle Sentence Transformers.
    
    Args:
        model_name: Nom du modèle HuggingFace à utiliser
        
    Returns:
        Modèle Sentence Transformers chargé
    """
    global _model
    
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Chargement du modèle: {model_name}")
            _model = SentenceTransformer(model_name)
            logger.info(f"Modèle chargé - Dimensions: {_model.get_sentence_embedding_dimension()}")
        except ImportError:
            raise ImportError(
                "sentence-transformers n'est pas installé. "
                "Installez-le avec: pip install sentence-transformers"
            )
    
    return _model

def generate_embeddings(
    texts: List[str], 
    batch_size: int = 32,
    show_progress: bool = True,
    normalize: bool = True
) -> np.ndarray:
    """
    Génère des embeddings pour une liste de textes.
    
    Args:
        texts: Liste de textes à vectoriser
        batch_size: Taille des batchs pour le traitement
        show_progress: Afficher la barre de progression
        normalize: Normaliser les vecteurs (recommandé pour la similarité cosinus)
        
    Returns:
        Array numpy de shape (n_texts, embedding_dim)
    """
    if not texts:
        logger.warning("Liste de textes vide")
        return np.array([])
    
    model = load_embedding_model()
    
    logger.info(f"Génération de {len(texts)} embeddings (batch_size={batch_size})")
    
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=normalize,
        convert_to_numpy=True
    )
    
    logger.info(f"Embeddings générés - Shape: {embeddings.shape}")
    
    return embeddings


def get_embedding_dimension() -> Optional[int]:
    """
    Retourne la dimension des embeddings du modèle chargé.
    
    Returns:
        Dimension des embeddings ou None si le modèle n'est pas chargé
    """
    if _model is None:
        return None
    return _model.get_sentence_embedding_dimension()