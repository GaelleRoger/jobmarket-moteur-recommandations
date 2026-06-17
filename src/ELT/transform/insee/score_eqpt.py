"""
Module de transformation : création du score d'équipements pour 10000 hab
"""
import math
import pandas as pd
import json
import logging
from bson import json_util
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

import sys

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))
from src.mongodb import get_mongo_client
from src.utils import save_json, DATA_PRO_INSEE_EQPT

def load_eqpt_insee(territory_code,db_name='job_market'):
    """
    Lit les collections brutes des équipements depuis MongoDB
    
    """
    logger.info("Lecture des collections brutes MongoDB...")

    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'eqpt_dept_insee'
    elif territory_code == 'REG':
        filename = 'eqpt_reg_insee'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    collname_raw = filename + "_raw"

    raw_coll = db[collname_raw]
    
    df_metadata = pd.DataFrame(list(db.eqpt_metadata_insee_raw.find({}, {'_id': 0})))
    list_eqpt_raw = list(raw_coll.find({}, {'_id': 0}))

    logger.info(f"{len(df_metadata)} métadonnées récupérées")
    logger.info(f"{len(list_eqpt_raw)} équipements par {territory_code} récupérés")

    #json_bse_dept = json.loads(list_eqpt_raw)

    """print(df_metadata)"""
    #print(list_eqpt_raw[:10])

    # Création d'un dataframe BSE DEPT
    records = []

    for obs in list_eqpt_raw:
        record = {
        'territory_type':territory_code,
        'territory': obs['dimensions']['GEO'].split('-')[-1],
        'type': obs['dimensions']['FACILITY_DOM'],
        'nb_equipements' : obs['measures']['OBS_VALUE_NIVEAU']['value']
        }
    
        records.append(record)

    df_eqpt = pd.DataFrame(records)

    return df_eqpt,df_metadata

    
def load_pop_insee(territory_code,db_name='job_market'):
    """
    Lit les collections brutes des populations depuis MongoDB
    
    """
    logger.info("Lecture des collections brutes MongoDB...")

    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'pop_dept_insee'
    elif territory_code == 'REG':
        filename = 'pop_reg_insee'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    collname_raw = filename + "_raw"

    raw_coll = db[collname_raw]
    
    list_pop_raw = list(raw_coll.find({}, {'_id': 0}))
    logger.info(f"{len(list_pop_raw)} populations par {territory_code} récupérés")
    #print(list_pop_raw[:10])

    # Transformation Population en DataFrame
    records=[]
    for obs in list_pop_raw:
        record = {
        'territory_type':territory_code,
        'territory': obs['dimensions']['GEO'].split('-')[-1],
        'population': obs['measures']['OBS_VALUE_NIVEAU']['value']
     }
        records.append(record)

    df_pop = pd.DataFrame(records)

    return df_pop

def calculer_note_sur_5(scores):
    """
    Convertit un array de scores en notes de 1 à 5 basées sur les quantiles.
    
    Args:
        scores: Series pandas contenant les scores
        
    Returns:
        Series pandas contenant les notes de 1 à 5
    """
    # Gérer les valeurs manquantes
    if scores.isna().all():
        return scores
    
    # Calculer les quantiles (20%, 40%, 60%, 80%)
    # Note 1: <= Q20, Note 2: Q20-Q40, Note 3: Q40-Q60, Note 4: Q60-Q80, Note 5: > Q80
    quantiles = scores.quantile([0.2, 0.4, 0.6, 0.8])
    
    def assign_note(score):
        if pd.isna(score):
            return None
        elif score <= quantiles[0.2]:
            return 1
        elif score <= quantiles[0.4]:
            return 2
        elif score <= quantiles[0.6]:
            return 3
        elif score <= quantiles[0.8]:
            return 4
        else:
            return 5
    
    return scores.apply(assign_note)


def calcul_score(territory_code):
    """
    Calcul le score des équipements pour 10000 habitants et la note sur 5
    
    """
    logger.info("Calcul du score d'équipements")

    # Mapping des catégories (libelle -> clé normalisée)
    CATEGORY_MAPPING = {
        "Services pour les particuliers": "services_particuliers",
        "Commerces": "commerces",
        "Enseignement": "enseignement",
        "Santé et action sociale": "sante_action_sociale",
        "Transports et déplacements": "transports_deplacements",
        "Sports, loisirs et culture": "sports_loisirs_culture",
        "Tourisme": "tourisme",
        "Total": "total",
    }

    df_eqpt,df_metadata = load_eqpt_insee(territory_code)
    df_pop = load_pop_insee(territory_code)

    # Jointure sur le territoire
    df_eqpt_complet = df_eqpt.merge(right=df_metadata, on = "type", how = "left")
    df_eqpt_pop = df_eqpt_complet.merge(right=df_pop, on = "territory", how = "inner")

    # On ne garde que les colonnes utiles
    df_eqpt_pop = df_eqpt_pop[["territory", "libelle", "nb_equipements", "population"]]

    # Normalisation du code département en string (utile pour DOM/TOM aussi)
    df_eqpt_pop["territory"] = df_eqpt_pop["territory"].astype(str)

    # Normalisation du libellé en clé
    df_eqpt_pop["cat_norm"] = df_eqpt_pop["libelle"].map(CATEGORY_MAPPING)

    # On suppose population constante par département dans ce fichier
    pop = df_eqpt_pop.groupby("territory")["population"].first()

    # Agrégation : somme des équipements par territoire / catégorie
    agg = (
        df_eqpt_pop.groupby(["territory", "cat_norm"])["nb_equipements"]
        .sum()
        .reset_index()
    )

    # Calcul du score pour 10 000 habitants
    agg = agg.merge(pop.rename("population"), on="territory", how="left")
    agg["score_10000hab"] = agg["nb_equipements"] / agg["population"] * 10000

    # Pivot : un département par ligne, colonnes par catégorie
    pivot_count = agg.pivot_table(
        index="territory",
        columns="cat_norm",
        values="nb_equipements",
        aggfunc="sum"
    )
    pivot_score = agg.pivot_table(
        index="territory",
        columns="cat_norm",
        values="score_10000hab",
        aggfunc="mean"
    )

    pivot_count.columns = [f"{c}_count" for c in pivot_count.columns]
    pivot_score.columns = [f"{c}_score_10000hab" for c in pivot_score.columns]

    # Calculer les notes sur 5 pour chaque catégorie
    pivot_note = pd.DataFrame(index=pivot_score.index)
    for cat in CATEGORY_MAPPING.values():
        score_col = f"{cat}_score_10000hab"
        if score_col in pivot_score.columns:
            pivot_note[f"{cat}_note_sur_5"] = calculer_note_sur_5(pivot_score[score_col])

    df_final = pd.concat([pop, pivot_count, pivot_score, pivot_note], axis=1).reset_index()
    df_final.rename(columns={"population": "population"}, inplace=True)

    #print(df_final.head(5))

    # -----------------------------
    # Construction des documents Mongo
    # -----------------------------


    docs = []
    for _, row in df_final.iterrows():
        territory = str(row["territory"])
        population = row["population"]

        services = {}
        for lib_norm in CATEGORY_MAPPING.values():
            count_col = f"{lib_norm}_count"
            score_col = f"{lib_norm}_score_10000hab"
            note_col = f"{lib_norm}_note_sur_5"

            count_val = row[count_col] if count_col in row else math.nan
            score_val = row[score_col] if score_col in row else math.nan
            note_val = row[note_col] if note_col in row else math.nan

            if not (pd.isna(count_val) and pd.isna(score_val) and pd.isna(note_val)):
                services[lib_norm] = {
                    "count": None if pd.isna(count_val) else float(count_val),
                    "score_10000hab": None if pd.isna(score_val) else float(score_val),
                    "note_sur_5": None if pd.isna(note_val) else int(note_val),
                }

        doc = {
            "_id": territory_code + territory,
            "territory_type": territory_code,
            "territory": territory,
            "population": None if pd.isna(population) else float(population),
            "services": services,
        }
        docs.append(doc)

    return docs

def load_score_mongo(territory_code,db_name='job_market'):
    """
    Insère le score des équipements vers MongoDB
    
    """
    logger.info("Envoi du score calculé vers MongoDB...")

    # Connexion MongoDB
    client = get_mongo_client()
    db = client[db_name]
    
    # Nom fichier selon le territoire choisi
    if territory_code == 'DEP':
        filename = 'score_eqpt_dept_insee'
    elif territory_code == 'REG':
        filename = 'score_eqpt_reg_insee'
    else:
        "Le code territoire doit être 'DEP' ou 'REG'"

    collname_pro = filename + "_pro"
    pro_coll = db[collname_pro]

    docs_to_insert = calcul_score(territory_code)
    
    # Insertion dans la collection de sortie
    if docs_to_insert:
        pro_coll.drop()
        pro_coll.insert_many(docs_to_insert)

    logger.info(f"{len(docs_to_insert)} documents insérés dans {collname_pro}")

    client.close()

    # Convertit les documents en JSON sérialisable
    docs_serializable = json.loads(json_util.dumps(docs_to_insert))

    # Sauvegarde en JSON
    filepath = save_json(docs_serializable, DATA_PRO_INSEE_EQPT, collname_pro)
    logger.info(f"Export JSON : {filepath.stat().st_size / 1024:.2f} KB")
    
    return filepath



if __name__ == "__main__":
    load_score_mongo('DEP')
    load_score_mongo('REG')