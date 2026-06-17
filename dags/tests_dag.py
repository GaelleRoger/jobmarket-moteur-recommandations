"""
DAG de test simple pour vérifier la configuration
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def test_mongodb_connection():
    """Test de connexion à MongoDB"""
    from pymongo import MongoClient
    
    mongo_user = os.getenv('MONGO_USER')
    mongo_password = os.getenv('MONGO_PASSWORD')
    mongo_host = os.getenv('MONGO_HOST', 'mongodb')
    mongo_port = os.getenv('MONGO_PORT', '27017')
    
    try:
        connection_string = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test de la connexion
        client.server_info()
        
        databases = client.list_database_names()
        print(f"✅ Connexion MongoDB réussie!")
        print(f"📊 Bases de données disponibles: {databases}")
        
        client.close()
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {str(e)}")
        raise

def test_elasticsearch_connection():
    """Test de connexion à Elasticsearch"""
    from elasticsearch import Elasticsearch
    
    es_host = os.getenv('ELASTICSEARCH_HOST', 'elasticsearch')
    es_port = os.getenv('ELASTICSEARCH_PORT', '9200')
    
    try:
        es = Elasticsearch([f"http://{es_host}:{es_port}"], request_timeout=5)
        
        if es.ping():
            info = es.info()
            print(f"✅ Connexion Elasticsearch réussie!")
            print(f"📊 Version: {info['version']['number']}")
            print(f"📊 Cluster: {info['cluster_name']}")
            
            # Lister les index existants
            indices = es.indices.get_alias(index="*")
            print(f"📊 Index disponibles: {list(indices.keys())}")
        else:
            print("❌ Impossible de ping Elasticsearch")
            raise Exception("Elasticsearch ping failed")
        
        es.close()
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion Elasticsearch: {str(e)}")
        raise

def test_environment_variables():
    """Vérifier que les variables d'environnement sont bien configurées"""
    required_vars = ['MONGO_USER', 'MONGO_PASSWORD', 'MONGO_DB', 'MONGO_HOST']
    
    print("🔍 Vérification des variables d'environnement...")
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Ne pas afficher le mot de passe en clair
            display_value = '***' if 'PASSWORD' in var else value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: NON DÉFINI")
            raise Exception(f"Variable d'environnement {var} non définie")
    
    print("✅ Toutes les variables d'environnement requises sont définies")
    return True

# Définition du DAG
with DAG(
    'test_connexions',
    default_args=default_args,
    description='DAG de test pour vérifier les connexions aux services',
    schedule_interval=None,  # Manuel uniquement
    start_date=days_ago(1),
    catchup=False,
    tags=['test', 'diagnostic'],
) as dag:
    
    # Tâche 1 : Vérifier les variables d'environnement
    test_env = PythonOperator(
        task_id='test_environment',
        python_callable=test_environment_variables,
    )
    
    # Tâche 2 : Vérifier les dépendances Python
    test_python_packages = BashOperator(
        task_id='test_python_packages',
        bash_command='''
        echo "📦 Vérification des packages Python installés..."
        python -c "import pymongo; print('✅ pymongo:', pymongo.__version__)"
        python -c "import elasticsearch; print('✅ elasticsearch:', elasticsearch.__version__)"
        python -c "import pandas; print('✅ pandas:', pandas.__version__)"
        python -c "import requests; print('✅ requests:', requests.__version__)"
        echo "✅ Tous les packages requis sont installés"
        '''
    )
    
    # Tâche 3 : Test MongoDB
    test_mongo = PythonOperator(
        task_id='test_mongodb',
        python_callable=test_mongodb_connection,
    )
    
    # Tâche 4 : Test Elasticsearch
    test_es = PythonOperator(
        task_id='test_elasticsearch',
        python_callable=test_elasticsearch_connection,
    )
    
    # Tâche 5 : Rapport final
    final_report = BashOperator(
        task_id='final_report',
        bash_command='''
        echo ""
        echo "=========================================="
        echo "✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS"
        echo "=========================================="
        echo ""
        echo "Le système est prêt à être utilisé !"
        echo ""
        '''
    )
    
    # Définir l'ordre d'exécution
    test_env >> test_python_packages >> [test_mongo, test_es] >> final_report