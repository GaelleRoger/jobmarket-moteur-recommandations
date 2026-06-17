"""
Services de calcul de similarité cosinus pour la recherche sémantique.
"""
import numpy as np

def normalize_vector(vec: np.ndarray) -> np.ndarray:
    """
    Normalise un vecteur avec la norme L2.
    
    Args:
        vec: Vecteur numpy à normaliser
        
    Returns:
        Vecteur normalisé (norme L2 = 1)
    """
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcule la similarité cosinus entre deux vecteurs.
    Les vecteurs doivent être normalisés au préalable.
    
    Args:
        vec1: Premier vecteur (normalisé)
        vec2: Deuxième vecteur (normalisé)
        
    Returns:
        Score de similarité cosinus (produit scalaire des vecteurs normalisés)
    """
    return float(np.dot(vec1, vec2))