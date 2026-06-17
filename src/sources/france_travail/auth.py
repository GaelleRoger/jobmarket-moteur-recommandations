"""
Authentification France Travail API.
Supporte différents scopes selon l'API utilisée.
"""
import os
import base64
import requests
import logging
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

# Scopes France Travail
FT_SCOPE_OFFRES = "api_offresdemploiv2 o2dsoffre"
FT_SCOPE_STATS = "offresetdemandesemploi api_stats-offres-demandes-emploiv1"
FT_SCOPE_REFERENTIEL = "api_referentielv1 nomenclatureRome"

def get_access_token(scope: str = FT_SCOPE_OFFRES) -> str:
    """
    Récupère un token d'accès pour l'API France Travail.
    
    Args:
        scope: Scope à utiliser (défaut: FT_SCOPE_OFFRES)
               Utiliser les constantes FT_SCOPE_* ou un scope personnalisé
    
    Returns:
        str: Token d'accès Bearer
        
    Raises:
        ValueError: Si les credentials sont manquants
        requests.HTTPError: Si la requête échoue
        
    Examples:
        >>> from sources.france_travail import get_access_token, FT_SCOPE_OFFRES, FT_SCOPE_STATS
        >>> token = get_access_token(FT_SCOPE_OFFRES)
        >>> token = get_access_token(FT_SCOPE_STATS)
    """
    token_url = os.getenv('FT_TOKEN_URL')
    client_id = os.getenv('FT_CLIENT_ID')
    client_secret = os.getenv('FT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("FT_CLIENT_ID et FT_CLIENT_SECRET manquants dans .env")
    
    if not token_url:
        raise ValueError("FT_TOKEN_URL manquant dans .env")
    
    # Encodage credentials
    credentials = f"{client_id}:{client_secret}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": scope
    }
    
    logger.info(f"Demande token France Travail (scope: {scope[:30]}...)")
    
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        
        access_token = response.json()["access_token"]
        logger.info("Token France Travail obtenu")
        
        return access_token
        
    except requests.HTTPError as e:
        logger.error(f"Erreur HTTP {response.status_code}: {response.text}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention du token: {e}")
        raise

