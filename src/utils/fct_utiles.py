## Import des librairies

import os
import requests
import json
import base64
import time
import pandas as pd
from datetime import datetime
##############################################################################################################################################  
## Déclarartion des décorateurs 
#################################
def verif_rslt(msg_ok="Succès 01", msg_err="Erreur lors de la requête"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            l_msg_ok = kwargs.get('msg_ok', msg_ok)
            l_msg_err = kwargs.get('msg_err', msg_err)
            response = func(*args, **kwargs)            
            if isinstance(response, requests.Response):
                if response.status_code in [200, 206]:
                    #print(f"{l_msg_ok}")
                    #rslt = response.json()
                    #return rslt
                    rslt = response.json()
                    return rslt
                else:
                    print(f"{l_msg_err} | Statut : {response.status_code}")
                    return None
            else:
                return response
        return wrapper
    return decorator

def check_file_json(msg_ok="Format JSON valide",msg_err="Le document n'est pas au format JSON"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            if response is None:
                return None   # l'autre décorateur a déjà traité le problème
            try:
                print(f"{msg_ok}")
                return response
            except ValueError:
                print(f"{msg_err} | Statut : {response.status_code}")
                return None
        return wrapper
    return decorator

#################################
## Déclarartion des Fonctions
#################################
# Fonctions génériques

# Fonctions spécifiques  
def get_colname(df_json, colname):
    if df_json is None:
        print("Erreur : le JSON est vide")
        return pd.DataFrame()
    if colname not in df_json:
        print(f"Erreur : la clé '{colname}' n'existe pas dans le JSON")
        return pd.DataFrame()
    df = pd.json_normalize(df_json[colname])
    return df

def filtrer_colonne(df, colonne, mots_inclus=None, mots_exclus=None):
    # Vérification de base
    if colonne not in df.columns:
        raise ValueError(f"La colonne '{colonne}' n'existe pas dans le DataFrame")
    # Filtre d'inclusion
    if mots_inclus:
        pattern_inclus = '|'.join(mots_inclus)
        filtre_inclus = df[colonne].str.contains(pattern_inclus, case=False, na=False)
    else:
        filtre_inclus = True
    # Filtre d'exclusion
    if mots_exclus:
        pattern_exclus = '|'.join(mots_exclus)
        filtre_exclus = ~df[colonne].str.contains(pattern_exclus, case=False, na=False)
    else:
        filtre_exclus = True
    # Appliquer les filtres
    df_filtre = df[filtre_inclus & filtre_exclus]
    return df_filtre.reset_index(drop=True)

def get_payload(param_terr,cd_terr,param_cd_rome):
    payload = {
                "codeTypeTerritoire": param_terr, #prend la valeur "REG" pour région ou "DEP" pour département
                "codeTerritoire": cd_terr, # code du territoire, par exemple '92' pour le département des Hauts-de-Seine
                "codeTypeActivite": "ROME",
                "codeActivite": param_cd_rome, # code Rome du métier recherché, par exemple "M1811" pour Data Engineer
                "codeTypePeriode": "ANNEE",
                "codeTypeNomenclature": "TYPE_TENSION",
                "dernierePeriode": True,
                "listeCodeNomenclature": ["PERSPECTIVE"]
            }
    return payload

def dedoublonner_offres(Dict_Data, RD_Key):
    unique_ligne = {Ligne[RD_Key]: Ligne for Ligne in Dict_Data}
    return list(unique_ligne.values()) 

def save_offers(rslt_data,pathfile,outputfilename,ext):
    os.makedirs(pathfile, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{pathfile}/{outputfilename}_{timestamp}.{ext}'   
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(rslt_data, f, ensure_ascii=False, indent=2)
    return filename

###################################################
# Applique le décorateur avec messages dynamiques 
###################################################
@verif_rslt(msg_ok="Succès", msg_err="Erreur lors de la requête")
def get_infos(url, headers, param_03, msg_ok, msg_err):
    if param_03 == 'None' or param_03 is None:
        param_03 = {}
    rslt = requests.post(url, headers=headers, **param_03)
    return rslt

@check_file_json(msg_ok="Format JSON valide",msg_err="Le document n'est pas au format JSON")
@verif_rslt(msg_ok="Récupération de données avec succès.", msg_err=f"Erreur lors de la récupération de données.")
def get_data(api_url,api_headers,param_03):
    if param_03 == 'None' or param_03 is None:
        param_03 = {}
    rslt = requests.get(api_url, headers=api_headers,params=param_03)
    return rslt

###################################################
# Fonction
###################################################
def get_access_token(url, client_id, client_secret, scope):
    # Encodage des identifiants en Base64
    credentials = f"{client_id}:{client_secret}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()
    # En-têtes de la requête
    headers = {"Authorization": f"Basic {b64_credentials}","Content-Type": "application/x-www-form-urlencoded"}
    # Autres paramètres
    data = {"grant_type": "client_credentials","scope": scope} 
    param_03 = {"data": data}
    msg_ok = "Token obtenu avec succès."
    msg_err = "Erreur lors de l'obtention du token."
    rslt_script = get_infos(url,headers,param_03,msg_ok=msg_ok,msg_err=msg_err).get("access_token")
    lines = rslt_script.splitlines()
    access_token = lines[-1] if lines else None
    api_headers = {"Authorization": f"Bearer {access_token}","Accept": "application/json"}
    rslt = {"msg_rslt": msg_ok,"access_token": access_token,"api_headers": api_headers}
    return rslt 

@verif_rslt(msg_ok="Récupération des offres par cd_rome réussie.", msg_err=f"Erreur lors de la récupération des offres par cd_rome.")
def collect_offers_by_rome(api_url,api_headers,rome_codes, range_end=149, sort=2, max_per_code=2000):
    all_offers = []   
    for rome_code in rome_codes:
        collected = 0       
        while collected < max_per_code:
            new_range_end = min(collected + range_end, max_per_code - 1)
            param = {"range": f"{collected}-{new_range_end}","sort": sort,"codeROME": rome_code}
            results = get_data(api_url,api_headers,param_03=param)           
            if not results:
                break
            # Extraire offres (gère dict ou list)
            resultats = results.get('resultats', [])
            offres = resultats.get('offres', []) if isinstance(resultats, dict) else resultats          
            if not offres:
                break
            # Garder seulement offres avec description
            all_offers.extend([o for o in offres if o.get('description', '').strip()])
            # Next itération        
            if len(offres) < int(range_end) + 1:
                break
            collected += len(offres)  
            time.sleep(0.3)   
    return all_offers
