# 💼 JobMarket — Analyse du Marché de l'Emploi en France

![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)
![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white)
![Airflow](https://img.shields.io/badge/airflow-orchestration-017CEE?logo=apacheairflow&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-en%20développement-yellow.svg)

## 📋 Description

**Problème résolu :** Comprendre les dynamiques du marché de l'emploi en France nécessite d'agréger des données hétérogènes (offres, tensions sectorielles, démographie) dispersées entre plusieurs APIs publiques et privées.

**Solution apportée :** Un pipeline ELT automatisé qui collecte, transforme et centralise les données de 5 sources (France Travail, Adzuna, JSearch, INSEE, Data.gouv), exposées via une API FastAPI et une interface Streamlit avec **recherche sémantoqie d'offres d'emplois** par similarité cosinus.

---

## 🎬 Démo

### Statistiques des offres

![Statistiques des offres](images/stats_offres.png)

### Moteur de recherche sémantique

![Moteur de recherche](images/moteur_recherche.png)

### Exemple de résultats

![Résultats de recherche](images/resultats_recherche.png)

---

## ⚡ Installation Rapide

**Prérequis :** Docker & Docker Compose installés.

```bash
# 1. Cloner le repository
git clone https://github.com/GaelleRoger/jobmarket-moteur-recommandations.git
cd jobmarket-moteur-recommandations

# 2. Première installation (build des conteneurs + initialisation)
./install.sh

# 3. Démarrages suivants
./start.sh
```

L'interface Streamlit est accessible sur `http://localhost:8501` et l'API sur `http://localhost:8000`.

---

## 🔧 Fonctionnalités

- **Recherche sémantique offres d'emploi** — recherche multi-critères (poste, localisation, secteur) agrégée depuis plusieurs sources. Similarité cosinus entre une requête et les offres via `sentence-transformers`
- **Visualisations interactives** — cartes, histogrammes et indicateurs de tension du marché du travail avec Plotly
- **Pipeline ELT orchestré** — extraction automatisée des données d'offres via Airflow, stockage MongoDB + indexation Elasticsearch
- **Données contextuelles INSEE** — population, équipements, communes pour enrichir les analyses géographiques

---

## 📊 Données & Résultats

### 📡 Sources intégrées

| Source         | Type de données                                      |
| -------------- | ---------------------------------------------------- |
| France Travail | Offres d'emploi, codes ROME, indicateurs de tension  |
| Adzuna         | Offres d'emploi (secteur privé)                      |
| JSearch        | Offres d'emploi internationales                      |
| INSEE          | Population, équipements par commune                  |
| Data.gouv      | Référentiel des communes françaises                  |

### 📁 Architecture des données

```plaintext
data/
├── raw/          # Données brutes par source
│   ├── adzuna/
│   ├── france_travail/
│   ├── insee_eqpt/
│   └── jsearch/
└── processed/    # Données transformées et unifiées
    └── unified/
```

---

## 🗂️ Structure du Projet

```plaintext
NOV25-BDE-JOBMARKET/
├── airflow/          # DAGs et configuration Airflow
├── src/
│   ├── ELT/          # Extract / Load / Transform par source
│   ├── api/          # Backend FastAPI + interface Streamlit
│   ├── pipelines/    # Scripts d'orchestration
│   └── models/       # Modèles de matching sémantique
├── docker-compose.yml
├── install.sh
└── start.sh
```

---

## 🛠️ Stack Technique

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=Python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat&logo=FastAPI&logoColor=white)
![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)
![MongoDB](https://img.shields.io/badge/-MongoDB-47A248?style=flat&logo=MongoDB&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/-Elasticsearch-005571?style=flat&logo=Elasticsearch&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/-Airflow-017CEE?style=flat&logo=ApacheAirflow&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat&logo=Docker&logoColor=white)
![HuggingFace](https://img.shields.io/badge/-HuggingFace-FFD21E?style=flat&logo=huggingface&logoColor=black)
![scikit-learn](https://img.shields.io/badge/-Scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![spaCy](https://img.shields.io/badge/-spaCy-09A3D5?style=flat&logo=spacy&logoColor=white)


---

## 👤 Contact

**Projet réalisé en équipe** dans le cadre du Bootcamp Data Engineering — [DataScientest](https://datascientest.com/).

**Contact** Gaëlle Roger

- 💼 **Recruteurs :** Disponible pour de nouvelles opportunités — [LinkedIn](https://www.linkedin.com/in/gaelle-roger/)
- 🤝 **Contributeurs :** Issues et Pull Requests bienvenues !

---

⭐ **Ce projet vous a plu ?** N'hésitez pas à laisser une étoile !
