# ============================================
# Stage 1 : Builder - Installation des dépendances
# ============================================
FROM apache/airflow:2.10.3-python3.12 AS builder

USER root

# Installer les dépendances de compilation nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copier requirements
COPY requirements.txt /requirements.txt

# Installer avec optimisations pour PyTorch CPU (SANS --user)
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu torch==2.5.1+cpu && \
    pip install --no-cache-dir \
    -r /requirements.txt \
    'flask-limiter[redis]' \
    'psycopg2-binary>=2.9.0'

# ============================================
# Stage 2 : Image finale légère
# ============================================
FROM apache/airflow:2.10.3-python3.12

USER root

# Installer uniquement les dépendances runtime (pas de build-essential)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Préparer les dossiers
RUN mkdir -p /opt/airflow/data/raw/insee_eqpt /opt/airflow/logs && \
    chown -R airflow:0 /opt/airflow/data /opt/airflow/logs && \
    chmod -R 775 /opt/airflow/data

USER airflow

# Copier les packages Python installés depuis le builder
# Les packages sont dans le site-packages du virtualenv d'Airflow
COPY --from=builder /home/airflow/.local/lib/python3.12/site-packages /home/airflow/.local/lib/python3.12/site-packages
COPY --from=builder /home/airflow/.local/bin /home/airflow/.local/bin

# S'assurer que les binaires sont dans le PATH
ENV PATH=/home/airflow/.local/bin:$PATH

WORKDIR /opt/airflow

# Variables d'environnement
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=""
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow:airflow@postgres/airflow"
ENV AIRFLOW__WEBSERVER__ENABLE_CELERY_LONG_POLL=True

# Optimisations PyTorch pour réduire l'utilisation mémoire
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false
