"""
Load : Copie des collections de MongoDB vers Elasticsearch
"""

import os
from datetime import datetime
import json
import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_path))
import logging
from src.mongodb import get_mongo_client
from src.esearch import connect_elasticsearch, create_index_mapping
from elasticsearch import helpers

collections_list = ['offres_unified',
'score_eqpt_dept_insee_pro',
'tension_dept_ft_pro']

#COLLECTION_NAME = 'tension_dept_ft_pro'
#INDEX_NAME = 'tension_dept_ft_pro'


def convert_objectid(doc):
    """Convertit les ObjectId MongoDB en strings pour Elasticsearch"""
    doc_id = None
    if '_id' in doc:
        doc_id = str(doc['_id'])
        # IMPORTANT : Retirer _id du document car c'est un champ de métadonnées ES
        del doc['_id']
   
    # Parcourir récursivement pour convertir tous les ObjectId
    for key, value in doc.items():
        if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = convert_objectid(value)[0]  # Récupérer seulement le doc, pas l'id
        elif isinstance(value, list):
            doc[key] = [convert_objectid(item.copy())[0] if isinstance(item, dict) else item for item in value]
   
    return doc, doc_id


def sync_collection_to_elasticsearch(mongo_client, es_client, collection_name, index_name, db_name: str = "job_market"):
    """Synchronise une collection MongoDB vers un index Elasticsearch"""
    try:
        # Récupérer la collection
        db = mongo_client[db_name]
        collection = db[collection_name]
       
        # Compter les documents
        total_docs = collection.count_documents({})
        print(f"\n📊 Nombre de documents dans '{collection_name}': {total_docs}")
       
        if total_docs == 0:
            print("⚠ Aucun document à copier")
            return
       
        # Créer l'index si nécessaire
        create_index_mapping(es_client, index_name)
       
        # Préparer les documents pour l'insertion en bulk
        def generate_actions():
            for doc in collection.find():
                # Faire une copie pour ne pas modifier l'original
                doc_copy = doc.copy()
                
                # Convertir les ObjectId en strings ET retirer _id du document
                doc_processed, doc_id = convert_objectid(doc_copy)
                
                # Préparer l'action pour le bulk
                # _id est passé comme paramètre, PAS dans _source
                yield {
                    "_index": index_name,
                    "_id": doc_id,
                    "_source": doc_processed  # Le document SANS le champ _id
                }
       
        # Insertion en bulk
        print(f"\n🔄 Début de la copie...")
        success, failed = helpers.bulk(
            es_client,
            generate_actions(),
            chunk_size=500,
            raise_on_error=False
        )
       
        print(f"\n✓ Copie terminée!")
        print(f"  - Documents copiés avec succès: {success}")
        if failed:
            print(f"  - Documents en échec: {len(failed)}")
       
        # Vérification
        es_client.indices.refresh(index=index_name)
        es_count = es_client.count(index=index_name)['count']
        print(f"\n📊 Vérification:")
        print(f"  - MongoDB: {total_docs} documents")
        print(f"  - Elasticsearch: {es_count} documents")
       
    except Exception as e:
        print(f"✗ Erreur lors de la synchronisation: {e}")
        raise


def main():
    """Fonction principale"""


    
    mongo_client = None
    es_client = None
    
    try:
        # Connexions
        mongo_client = get_mongo_client()
        es_client = connect_elasticsearch()
        
        for coll in collections_list:
            COLLECTION_NAME = coll
            INDEX_NAME = coll

            print("=" * 60)
            print("SYNCHRONISATION MONGODB → ELASTICSEARCH")
            print("=" * 60)
            print(f"Collection: {COLLECTION_NAME}")
            print(f"Index: {INDEX_NAME}")
            print("=" * 60)

            # Synchronisation
            sync_collection_to_elasticsearch(
                mongo_client,
                es_client,
                COLLECTION_NAME,
                INDEX_NAME
            )
        
            print("\n" + "=" * 60)
            print("✓ SYNCHRONISATION TERMINÉE AVEC SUCCÈS")
            print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ ERREUR: {e}")
        print("=" * 60)
            
    finally:
        # Fermeture des connexions
        if mongo_client:
            mongo_client.close()
            print("\n✓ Connexion MongoDB fermée")


if __name__ == "__main__":
    main()