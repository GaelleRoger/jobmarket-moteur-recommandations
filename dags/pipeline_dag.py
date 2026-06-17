"""
DAG Pipeline - Orchestration des scripts ETL
Ce DAG orchestre l'exécution des scripts situés dans PROJET/src/
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

# Ajouter le chemin vers le dossier src pour importer les scripts
# Ajuster le chemin selon votre structure de dossiers
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PIPELINE_PATH = os.path.join(PROJECT_ROOT, 'src', 'pipelines')
sys.path.insert(0, PIPELINE_PATH)

# Configuration par défaut du DAG
default_args = {
    'owner': 'team-job-market',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# Définition du DAG
dag = DAG(
    'pipeline_etl_jobmarket',
    default_args=default_args,
    description='Pipeline ETL',
    schedule_interval='0 2 * * *',  # Tous les jours à 2h du matin
    start_date=datetime(2026, 1, 28),
    catchup=False,
    tags=['etl', 'pipeline', 'mongodb'],
)


extract_task_bash = BashOperator(
    task_id='extract_data',
    bash_command=(
        f'export PYTHONPATH=/opt/airflow:$PYTHONPATH && '
        f'cd {PIPELINE_PATH} && '
        'python3 01_extract.py'
    ),
    dag=dag,
)

load_task_bash = BashOperator(
    task_id='load_mongodb',
    bash_command=(
        f'export PYTHONPATH=/opt/airflow:$PYTHONPATH && '
        f'cd {PIPELINE_PATH} && '
        'python3 02_load_raw_mongodb.py'
    ),
    dag=dag,
)

transform_task_bash = BashOperator(
    task_id='transform_data',
    bash_command=(
        f'export PYTHONPATH=/opt/airflow:$PYTHONPATH && '
        f'cd {PIPELINE_PATH} && '
        'python3 03_transform.py'
    ),
    dag=dag,
)

merge_task_bash = BashOperator(
    task_id='merge_offers',
    bash_command=(
        f'export PYTHONPATH=/opt/airflow:$PYTHONPATH && '
        f'cd {PIPELINE_PATH} && '
        'python3 04_merge.py'
    ),
    dag=dag,
)

embeddings_task_bash = BashOperator(
    task_id='enrich_embeddings',
    bash_command=(
        f'export PYTHONPATH=/opt/airflow:$PYTHONPATH && '                            
        f'cd {PIPELINE_PATH} && '
        'python3 05_embeddings.py'
    ),
    dag=dag,
)

elasticsearch_task_bash = BashOperator(
    task_id='index_elasticsearch',
    bash_command=(
        f'export PYTHONPATH=/opt/airflow:$PYTHONPATH && '                            
        f'cd {PIPELINE_PATH} && '
        'python3 06_index_elasticsearch.py'
    ),
    dag=dag,
)

# Définir la dépendance
extract_task_bash >> load_task_bash >> transform_task_bash >> merge_task_bash >> embeddings_task_bash >> elasticsearch_task_bash
