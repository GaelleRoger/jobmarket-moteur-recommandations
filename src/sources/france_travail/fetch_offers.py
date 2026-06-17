"""
Appels API France Travail pour récupération des offres.
"""
import os
import time
import logging
import requests
from typing import List, Dict
from dotenv import load_dotenv
from .auth import get_access_token, FT_SCOPE_OFFRES
load_dotenv()
logger = logging.getLogger(__name__)

def fetch_offers(rome_codes: List[str], max_per_code: int = 2000) -> List[Dict]:
    """
    Récupère les offres depuis l'API France Travail.
    
    Args:
        rome_codes: Liste des codes ROME à récupérer
        max_per_code: Nombre max d'offres par code ROME
        
    Returns:
        List[Dict]: Liste de toutes les offres collectées
    """
    logger.info(f"Collecte des offres pour {len(rome_codes)} code(s) ROME")
    
    # Token
    access_token = get_access_token(FT_SCOPE_OFFRES)
    
    # Configuration
    offers_url = os.getenv('FT_OFFERS_URL')
    if not offers_url:
        raise ValueError("FT_OFFERS_URL manquant dans .env")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Collecte
    all_offers = []
    
    for rome_code in rome_codes:
        logger.info(f"Code ROME: {rome_code}")
        collected = 0
        
        while collected < max_per_code:
            range_end = min(collected + 149, max_per_code - 1)
            params = {
                'range': f'{collected}-{range_end}',
                'sort': 2,
                'codeROME': rome_code
            }
            
            try:
                response = requests.get(offers_url, headers=headers, params=params)
                
                if response.status_code not in [200, 206]:
                    logger.warning(f"Erreur API: {response.status_code}")
                    break
                
                results = response.json()
                resultats = results.get('resultats', [])
                offres = resultats.get('offres', []) if isinstance(resultats, dict) else resultats
                
                if not offres:
                    break
                
                # Garder seulement offres avec description
                offres_valides = [o for o in offres if o.get('description', '').strip()]
                all_offers.extend(offres_valides)
                
                collected += len(offres)
                logger.info(f"  {len(offres)} offres (total: {collected})")
                
                if len(offres) < 150:
                    break
                
                time.sleep(0.3)
                
            except requests.RequestException as e:
                logger.error(f"Erreur requête: {e}")
                break
    
    logger.info(f"Total: {len(all_offers)} offres collectées")
    return all_offers
