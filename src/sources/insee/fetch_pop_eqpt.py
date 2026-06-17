"""
Appels API INSEE pour récupération de la population et des équipements urbains
"""
import os
import json
import time
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning
from typing import List, Dict

logger = logging.getLogger(__name__)

INSEE_EQPT_URL="https://api.insee.fr/melodi/data/DS_BPE?FACILITY_SDOM=_T&FACILITY_TYPE=_T&TIME_PERIOD=2024&GEO="
INSEE_POP_URL="https://api.insee.fr/melodi/data/DS_RP_POPULATION_COMP?SEX=_T&TIME_PERIOD=2022&PCS=_T&AGE=Y_GE15&GEO="

def fetch_equipements(territory_code: str):
    """
    Récupère la liste des équipements urbains par territoire
    
    Args:
        territory_code : "DEP" pour département ou "REG" pour région
        
    Returns:

    """
    logger.info(f"Collecte des équipements par {territory_code}")
    
    # Désactiver l'avertissement pour éviter qu'il ne s'affiche dans la console (pas de token pour INSEE)
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    #Configuration
    api_url = INSEE_EQPT_URL + territory_code
    
    get_data = requests.get(api_url, verify= False)
    data_from_net = get_data.content
    json_bse = json.loads(data_from_net)
    
    logger.info(f"Total: {len(json_bse)} {territory_code} collectés")
    return json_bse['observations']


def fetch_population(territory_code: str):
    """
    Récupère la liste de la pôpulation active par territoire
    
    Args:
        territory_code : "DEP" pour département ou "REG" pour région
        
    Returns:

    """
    logger.info(f"Collecte de la population par {territory_code}")
    
    # Désactiver l'avertissement pour éviter qu'il ne s'affiche dans la console (pas de token pour INSEE)
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    #Configuration
    api_url = INSEE_POP_URL + territory_code
    
    get_data = requests.get(api_url, verify= False)
    data_from_net = get_data.content
    json_pop = json.loads(data_from_net)
    
    logger.info(f"Total: {len(json_pop)} {territory_code} collectés")
    return json_pop['observations']

def fetch_eqpt_metadata(): #pas d'URL pour télécharger le dsv, on le reconstruit directement
    import pandas as pd

    # Création du DataFrame
    data = {
        "type": ["_T", "A", "B", "C", "D", "E", "F", "G"],
        "libelle": [
            "Total",
            "Services pour les particuliers",
            "Commerces",
            "Enseignement",
            "Santé et action sociale",
            "Transports et déplacements",
            "Sports, loisirs et culture",
            "Tourisme"
        ],
        "libelle_anglais": [
            "Total",
            "Particular services",
            "Shops",
            "Education",
            "Health and social action",
            "Transport and travel",
            "Sports, leisure and culture",
            "Tourism"
        ]
    }

    df = pd.DataFrame(data)
    return df

