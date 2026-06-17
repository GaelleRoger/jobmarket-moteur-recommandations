# 💼 Portail Emploi - Application Streamlit

Application Streamlit pour explorer et analyser le marché de l'emploi en France.

## 📋 Prérequis

- Python 3.8+
- Elasticsearch en cours d'exécution sur `http://localhost:9200`
- Les données indexées dans Elasticsearch

## 🚀 Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

## 🏃 Démarrage

### Méthode 1 : Utiliser les scripts de démarrage

#### Sur Linux/Mac :
```bash
chmod +x start.sh
./start.sh
```

#### Sur Windows :
```bash
start.bat
```

### Méthode 2 : Démarrage manuel

#### Terminal 1 - Démarrer l'API FastAPI
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Démarrer Streamlit
```bash
streamlit run streamlit_app.py
```

## 🌐 Accès aux applications

- **API FastAPI** : http://localhost:8000
- **Documentation API (Swagger)** : http://localhost:8000/docs
- **Application Streamlit** : http://localhost:8501

## 📊 Fonctionnalités

### 1. Dashboard Statistiques
- Nombre total d'offres d'emploi
- Répartition des offres par département (graphiques et tableaux)
- Répartition des offres par région (graphiques en camembert)
- Top des compétences les plus demandées

### 2. Recherche par Département
- Recherche d'offres par code département
- Pagination des résultats
- Affichage détaillé de chaque offre avec :
  - Titre et employeur
  - Type de contrat
  - Localisation complète
  - Expérience requise
  - Salaire
  - Compétences demandées
  - Lien de candidature

### 3. Recherche par Mots-Clés
- Recherche d'offres par mots-clés
- Retour d'une offre aléatoire parmi les résultats
- Affichage des indicateurs :
  - **Tension du marché** : ratio offre/demande d'emploi
  - **Scores d'équipements** : qualité de vie du territoire (services, commerces, santé, transports, etc.)
- Graphique radar des équipements du département

## 🔧 Configuration

### Modifier l'URL de l'API

Dans `streamlit_app.py`, ligne 28 :
```python
API_BASE_URL = "http://localhost:8000"
```

### Modifier les indices Elasticsearch

Dans `main.py` :
```python
ES_HOST = "http://localhost:9200"
ES_INDEX = "offres_unified"
ES_TENSION_INDEX = "tension_dept_ft_pro"
ES_EQPT_INDEX = "score_eqpt_dept_insee_pro"
```

## 📡 Endpoints API

- `GET /health` - Vérifier l'état de l'API
- `GET /stats/total` - Nombre total d'offres
- `GET /stats/by_department` - Statistiques par département
- `GET /stats/by_region` - Statistiques par région
- `GET /stats/top_competences` - Top des compétences
- `GET /job_dept/?code_dep={code}` - Offres par département
- `POST /job_search` - Recherche d'offres par mots-clés

## 🎨 Personnalisation

### Modifier les couleurs et le style

Éditez la section CSS dans `streamlit_app.py` (lignes 18-40) :
```python
st.markdown("""
    <style>
    .main-header {
        color: #1f77b4;  /* Modifier cette couleur */
    }
    </style>
""", unsafe_allow_html=True)
```

### Modifier les limites de pagination

Dans les fonctions `page_search_by_department()` et autres, ajustez les valeurs :
```python
limit = st.number_input(
    "Offres par page",
    min_value=1,
    max_value=100,  # Modifier cette limite
    value=10
)
```

## 🐛 Dépannage

### L'API n'est pas accessible
- Vérifiez qu'Elasticsearch est démarré : `curl http://localhost:9200`
- Vérifiez que l'API FastAPI est démarrée : `curl http://localhost:8000/health`
- Vérifiez les logs de l'API pour voir les erreurs

### Streamlit ne se connecte pas à l'API
- Vérifiez l'URL dans `API_BASE_URL`
- Vérifiez qu'il n'y a pas de problème de CORS (ajouter middleware CORS dans FastAPI si nécessaire)

### Ajout du middleware CORS (si nécessaire)

Dans `main.py`, ajouter :
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📝 Notes

- Le cache Streamlit est configuré pour 5 minutes (300s) pour les données temps réel et 10 minutes (600s) pour les statistiques
- Les données sont récupérées en temps réel depuis Elasticsearch
- La pagination est gérée côté client via `st.session_state`

## 🤝 Contribution

Pour contribuer :
1. Forkez le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/amelioration`)
5. Créez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.
