"""
Gestion de la connexion Elasticsearch
"""

from elasticsearch import Elasticsearch
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
from .config import ESEARCH_CONFIG

ES_HOST = ESEARCH_CONFIG["host"]
ES_PORT = ESEARCH_CONFIG["port"]
ES_USER = ESEARCH_CONFIG.get("user", "elastic")
ES_PASSWORD = ESEARCH_CONFIG.get("password", None)
ES_USE_SSL = ESEARCH_CONFIG.get("use_ssl", False)
ES_VERIFY_CERTS = ESEARCH_CONFIG.get("verify_certs", False)

def connect_elasticsearch():
    """Connexion à Elasticsearch avec support ES 8.x"""
    try:
        url = f"{'https' if ES_USE_SSL else 'http'}://{ES_HOST}:{ES_PORT}"
        print(f"\n🔍 Tentative de connexion à Elasticsearch:")
        print(f"   URL: {url}")
        print(f"   Host: {ES_HOST}")
        print(f"   Port: {ES_PORT}")
        print(f"   SSL: {ES_USE_SSL}")
        print(f"   User: {ES_USER if ES_PASSWORD else 'Aucune authentification'}")
        
        # Configuration de la connexion selon la version ES
        es_config = {
            "hosts": [url],
            "request_timeout": 10,
            "max_retries": 3,
            "retry_on_timeout": True
        }
        
        # Ajouter l'authentification si mot de passe fourni
        if ES_PASSWORD:
            es_config["basic_auth"] = (ES_USER, ES_PASSWORD)
            print(f"   → Authentification activée")
        else:
            print(f"   → Mode sans authentification (dev)")
        
        # Gestion SSL pour ES 8.x
        if ES_USE_SSL:
            es_config["verify_certs"] = ES_VERIFY_CERTS
            if not ES_VERIFY_CERTS:
                print(f"   ⚠ Vérification SSL désactivée")
        
        # Tentative de connexion
        print(f"\n⏳ Connexion en cours...")
        es = Elasticsearch(**es_config)
        
        # Test de ping
        if es.ping():
            print(f"✓ Connexion à Elasticsearch réussie")
            
            # Informations sur le cluster
            try:
                info = es.info()
                print(f"   Version: {info['version']['number']}")
                print(f"   Cluster: {info['cluster_name']}")
            except Exception as e:
                print(f"   (Impossible d'obtenir les infos du cluster: {e})")
            
            return es
        else:
            raise Exception("Le ping a échoué - Elasticsearch ne répond pas")
            
    except Exception as e:
        print(f"\n✗ Erreur de connexion à Elasticsearch:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")
        
        # Messages d'aide spécifiques
        error_msg = str(e).lower()
        if "unauthorized" in error_msg or "401" in error_msg:
            print(f"\n💡 Problème d'authentification détecté!")
            print(f"   Solution 1: Récupérer le mot de passe elastic:")
            print(f"   → docker exec -it job_market_elasticsearch bin/elasticsearch-reset-password -u elastic")
            print(f"\n   Solution 2: Désactiver la sécurité (dev uniquement):")
            print(f"   → Voir les instructions ci-dessous")
        elif "connection" in error_msg or "refused" in error_msg:
            print(f"\n💡 Problème de connexion!")
            print(f"   → Vérifiez que le container est démarré: docker ps")
        
        print(f"\n📋 Vérifications à faire:")
        print(f"   1. Container actif: docker ps | grep elasticsearch")
        print(f"   2. Test curl: curl http://localhost:9200")
        print(f"   3. Vérifiez votre .env (voir config ci-dessous)")
        
        raise



"""def connect_elasticsearch():

    try:
        es = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
        # Test de connexion
        if es.ping():
            print(f"✓ Connexion à Elasticsearch réussie")
            return es
        else:
            raise Exception("Impossible de se connecter à Elasticsearch")
    except Exception as e:
        print(f"✗ Erreur de connexion à Elasticsearch: {e}")
        raise"""

def create_index_mapping(es, index_name):
    """Crée l'index Elasticsearch avec un mapping dynamique"""
    if es.indices.exists(index=index_name):
        print(f"⚠ L'index '{index_name}' existe déjà")
        es.indices.delete(index=index_name)
        print(f"✓ Index '{index_name}' supprimé")

   
    # Mapping de base - peut être personnalisé selon vos besoins
    mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"}
            }
        }
    }
   
    es.indices.create(index=index_name, body=mapping)
    print(f"✓ Index '{index_name}' créé")
