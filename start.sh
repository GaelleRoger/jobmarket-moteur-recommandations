#!/bin/bash

# Script de démarrage du projet ETL Offres d'Emploi
# Ce script configure et démarre tous les services nécessaires

set -e

echo "🚀 Démarrage du projet Jobmarket"
echo "=========================================================="

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Initialiser Airflow
echo "🔧 Initialisation d'Airflow..."
docker compose up airflow-init

# Démarrer tous les services
echo "🚀 Démarrage de tous les services..."
docker compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 15

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
echo "   - MongoDB: http://localhost:27017"
echo "   - FastAPI: http://localhost:8000/docs#/"
echo "   - Streamlit: http://localhost:8501"
echo ""
echo -e "${GREEN}🎉 Installation terminée avec succès !${NC}"