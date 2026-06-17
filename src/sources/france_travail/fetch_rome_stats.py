"""
Appels API France Travail pour récupération des offres.
"""
import os
import pandas as pd
import time
import logging
import requests
from typing import List, Dict
from dotenv import load_dotenv
from .auth import get_access_token, FT_SCOPE_STATS
load_dotenv()
logger = logging.getLogger(__name__)

def fetch_territory(territory_code: str):
    """
    Récupère la liste des territoires depuis France Travail
    
    Args:
        territory_code : "DEP" pour département ou "REG" pour région
        
    Returns:

    """
    logger.info(f"Collecte des territoires {territory_code}")
    
    # Token
    access_token = get_access_token(FT_SCOPE_STATS)
    
    # Configuration
    terr_url = os.getenv('FT_TERR_URL') + territory_code
    if not terr_url:
        raise ValueError("FT_TERR_URL manquant dans .env")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Collecte
    
    # Effectuer la requête GET
    response = requests.get(terr_url, headers=headers)

    # Vérification de la réponse
    if response.status_code == 200:
        # Si la réponse est en JSON
        try:
            data = response.json()
        except ValueError:
            # Si la réponse est en XML
            print("Réponse en XML :")
            print(response.text)
    else:
        print("Erreur lors de la collecte des territoires :")
        print("Statut :", response.status_code)
        print("Réponse :", response.text)

    terr_df = pd.json_normalize(data['territoires'])
    
    logger.info(f"Total: {len(terr_df)} {territory_code} collectés")
    return terr_df


def fetch_rome_codes():
    """
    Récupère la liste des codes ROME et le libellé activité associé
    
    Args:
        territory_code : "DEP" pour département ou "REG" pour région
        
    Returns:

    """
    logger.info(f"Collecte des codes ROME")
    
    # Token
    access_token = get_access_token(FT_SCOPE_STATS)
    
    # Configuration
    rome_url = os.getenv('FT_ROME_ACTIVITY_URL')
    if not rome_url:
        raise ValueError("FT_ROME_ACTIVITY_URL manquant dans .env")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Collecte
    
    # Effectuer la requête GET
    response = requests.get(rome_url, headers=headers)

    # Vérification de la réponse
    if response.status_code == 200:
        # Si la réponse est en JSON
        try:
            data = response.json()
        except ValueError:
            # Si la réponse est en XML
            print("Réponse en XML :")
            print(response.text)
    else:
        print("Erreur lors de la collecte des codes ROME :")
        print("Statut :", response.status_code)
        print("Réponse :", response.text)

    # Filtrer les activités pour ne garder que celles avec "codeTypeActivite": "ROME"
    activites_filtrees = [activite for activite in data["activites"]
    if activite.get("codeTypeActivite") == "ROME"]

    # Créer un nouveau dictionnaire avec uniquement les activités filtrées
    data_filtree = {"activites": activites_filtrees}

    
    logger.info(f"Total: {len(data_filtree["activites"])} codes ROME collectés")
    return data_filtree["activites"]


def fetch_tension_indicator(territory_code, rome_codes):
    """
    Récupère l'indicateur de tension pour un métier donné (code rome) et un territoire donné (département ou région)
    
    Args:
        territory_code : "DEP" pour département ou "REG" pour région
        terr_list : liste des codes territoires
        rome_codes : liste des codes ROME
        
    Returns:

    """
    logger.info(f"Collecte des indicateurs de tension")

    # Récupération des territoires
    terr_df = fetch_territory(territory_code)
    terr_list = list(terr_df['codeTerritoire'])
    
    # Token
    access_token = get_access_token(FT_SCOPE_STATS)
    
    # Configuration
    tension_url = os.getenv('FT_TENSION_URL')
    if not tension_url:
        raise ValueError("FT_TENSION_URL manquant dans .env")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        "Content-Type": "application/json",
        'Accept': 'application/json'
    }
    
    # Initialisation de la liste pour stocker tous les résultats
    tous_les_resultats = []

    for terr in terr_list:
        for r in rome_codes:
            

            payload = {
                "codeTypeTerritoire": territory_code,
                "codeTerritoire": terr,
                "codeTypeActivite": "ROME",
                "codeActivite": r,
                "codeTypePeriode": "ANNEE",
                "codeTypeNomenclature": "TYPE_TENSION",
                "dernierePeriode": True,
                "listeCodeNomenclature": ["PERSPECTIVE"]
            }

            response = requests.post(tension_url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                # Ajouter les données à la liste globale
                tous_les_resultats.append({
                    "type_territoire":territory_code,
                    "code_territoire": terr,
                    "code_ROME": r,
                    "données": data
                })
            else:
                print(f"Erreur pour le territoire {territory_code} {terr} et le code ROME {r}: {response.status_code}, {response.text}")

    
    logger.info(f"Total: {len(tous_les_resultats)} indicateurs de tension collectés")
    return tous_les_resultats
