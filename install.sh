#!/bin/bash

# Script de premier démarrage du projet Job market
# Ce script configure et démarre tous les services nécessaires

set -e

echo "🚀 Installation du projet Jobmarket"
echo "=========================================================="

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Attribution des droits
echo "Attribution des droits aux dossiers Airflow..."
sudo chmod -R 777 logs/
sudo chmod -R 777 dags/
sudo chmod -R 777 plugins/
sudo chmod -R 777 data/

# Variables d'environnement pour Airflow
echo "Ecriture des variables d'environnement Airflow..."
echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" >> .env
echo "AIRFLOW_FERNET_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env

# Construire les images Docker
echo "🏗️  Construction des images Docker..."
docker compose build --no-cache

# Initialiser Airflow
echo "🔧 Initialisation d'Airflow..."
docker compose up airflow-init

# Démarrer tous les services
echo "🚀 Démarrage de tous les services..."
docker compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérifier l'état des services
echo ""
echo "📊 État des services:"
docker compose ps

echo ""
echo -e "${GREEN}✅ Tous les services sont démarrés !${NC}"
echo ""
echo "🌐 Accès aux services:"
echo "   - Airflow UI: http://localhost:8080 (admin/admin)"
echo "   - Kibana: http://localhost:5601"
echo "   - Elasticsearch: http://localhost:9200"
echo "   - MongoDB: mongodb://localhost:27017"
echo ""
echo -e "${GREEN}🎉 Installation terminée avec succès !${NC}"