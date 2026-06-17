#!/bin/bash

echo "================================================"
echo "  Démarrage du Portail Emploi"
echo "================================================"
echo ""

# Vérifier si Elasticsearch est accessible
echo "🔍 Vérification d'Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null; then
    echo "✅ Elasticsearch est accessible"
else
    echo "❌ Elasticsearch n'est pas accessible sur http://localhost:9200"
    echo "   Veuillez démarrer Elasticsearch avant de continuer"
    exit 1
fi

echo ""
echo "🚀 Démarrage de l'API FastAPI..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Démarrer l'API en arrière-plan
uvicorn main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Attendre que l'API soit prête
echo "⏳ Attente du démarrage de l'API..."
sleep 5

# Vérifier si l'API est accessible
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API démarrée avec succès"
else
    echo "❌ Erreur lors du démarrage de l'API"
    kill $API_PID
    exit 1
fi

echo ""
echo "🎨 Démarrage de Streamlit..."
echo "   URL: http://localhost:8501"
echo ""
echo "================================================"
echo "  Applications démarrées !"
echo "================================================"
echo ""
echo "  📡 API FastAPI:  http://localhost:8000"
echo "  📊 Streamlit:    http://localhost:8501"
echo ""
echo "  Pour arrêter, appuyez sur Ctrl+C"
echo ""

# Démarrer Streamlit
streamlit run streamlit_app.py

# Quand Streamlit s'arrête, tuer l'API
kill $API_PID
