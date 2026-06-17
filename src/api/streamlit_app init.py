import requests
import pandas as pd
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any, List
import os

# Configuration de la page
st.set_page_config(
    page_title="Projet Job Market - NOV25 Bootcamp DE",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de l'API

#API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000") # pour que ça tourne dans Docker
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Style CSS personnalisé
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .job-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .similarity-badge {
        background-color: #1f77b4;
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 0.3rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


# ============== FONCTIONS UTILITAIRES POUR APPELER L'API ==============
@st.cache_data(ttl=300)
def check_api_health() -> bool:
    """Vérifie que l'API est accessible"""
    try:
        # Augmentez le timeout car le premier appel réveille parfois les modèles ML
        response = requests.get(f"{API_BASE_URL}/health", timeout=15)
        return response.status_code == 200
    except Exception as e:
        # Ceci s'affichera dans vos logs Docker
        print(f"DEBUG CONNECTION ERROR: {e}")
        return False

# ============== FONCTIONS POUR LES STATISTIQUES ==============

@st.cache_data(ttl=600)
def get_total_jobs() -> Optional[Dict[str, Any]]:
    """Récupère le nombre total d'offres"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/stats/total", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération du total : {e}")
        return None


@st.cache_data(ttl=600)
def get_jobs_by_department(limit: int = 100) -> Optional[Dict[str, Any]]:
    """Récupère les statistiques par département"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/stats/by_department",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération des stats départementales : {e}")
        return None


@st.cache_data(ttl=600)
def get_jobs_by_region(limit: int = 100) -> Optional[Dict[str, Any]]:
    """Récupère les statistiques par région"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/stats/by_region",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération des stats régionales : {e}")
        return None


@st.cache_data(ttl=600)
def get_top_competences(limit: int = 50) -> Optional[Dict[str, Any]]:
    """Récupère les compétences les plus demandées"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/stats/top_competences",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération des compétences : {e}")
        return None


# ============== FONCTIONS POUR LA RECHERCHE D'OFFRES ==============

def get_jobs_by_dept_code(codedep: str, limit: int = 10, offset: int = 0) -> Optional[Dict[str, Any]]:
    """Récupère les offres d'un département spécifique"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/job_dept/",
            params={"codedep": codedep, "limit": limit, "offset": offset},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération des offres : {e}")
        return None


def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    """Récupère une offre par son ID"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs/{job_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.warning(f"Aucune offre trouvée avec l'ID : {job_id}")
            return None
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération de l'offre : {e}")
        return None

@st.cache_data(ttl=1800)
def semantic_search(text: str, geo_filter: Dict[str, Any], top_k: int = 10, geo_strategy: str = "fallback") -> Optional[Dict[str, Any]]:
    """Recherche sémantique d'offres avec filtre géographique"""
    try:
        payload = {
            "text": text,
            "top_k": top_k,
            "geo": geo_filter,
            "geo_strategy": geo_strategy
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/search/semantic",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.warning("Aucune offre trouvée pour cette recherche et ce filtre géographique")
            return None
        elif response.status_code == 422:
            error_detail = response.json().get('detail', 'Erreur de validation')
            st.error(f"Erreur de requête : {error_detail}")
            return None
        return None
    except Exception as e:
        st.error(f"Erreur lors de la recherche sémantique : {e}")
        return None

# ============== FONCTIONS POUR LA SIMILARITE COSINUS ==============
@st.cache_data(ttl=1800)
def cosine_similarity_search(
    text: str,
    top_k: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Recherche des similarités cosinus à partir d'un texte
    Route API : /api/v1/ml/similarity/cosine/compare
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ml/similarity/cosine/compare",
            json={
                "text": text,
                "top_k": top_k
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json()

        st.error(f"Erreur API Similarité : {response.status_code}")
        return None

    except Exception as e:
        st.error(f"Erreur lors de la recherche de similarité cosinus : {e}")
        return None

def split_similarity_results(items: List[Dict[str, Any]]):
    manual = [i for i in items if i["method"] == "manual"]
    native = [i for i in items if i["method"] == "native"]

    manual = sorted(manual, key=lambda x: x["rank"])
    native = sorted(native, key=lambda x: x["rank"])

    return manual, native

# ============== FONCTIONS D'AFFICHAGE ==============

def display_job_card(job: Dict[str, Any], show_full: bool = False, similarity_score: Optional[float] = None):
    """Affiche une carte d'offre d'emploi"""
    with st.container():
        st.markdown('<div class="job-card">', unsafe_allow_html=True)
        
        # Score de similarité si disponible
        if similarity_score is not None:
            st.markdown(
                f'<div class="similarity-badge">Score de similarité : {similarity_score:.3f}</div>',
                unsafe_allow_html=True
            )
        
        # Titre et employeur
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {job.get('title', 'N/A')}")
            if job.get('employer'):
                st.markdown(f"**Employeur :** {job['employer']}")
        
        with col2:
            if job.get('typeContrat'):
                st.markdown(f"**Contrat :** {job['typeContrat']}")
        
        # ID de l'offre
        if job.get('id'):
            st.markdown(f"**ID :** `{job['id']}`")
        
        # Localisation
        if job.get('lieuTravail'):
            lieu = job['lieuTravail']
            location_parts = []
            if lieu.get('libCom'):
                location_parts.append(lieu['libCom'])
            if lieu.get('libDep'):
                location_parts.append(lieu['libDep'])
            if lieu.get('libReg'):
                location_parts.append(lieu['libReg'])
            
            if location_parts:
                st.markdown(f"📍 **Localisation :** {', '.join(location_parts)}")
        
        # Informations supplémentaires
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if job.get('experienceLibelle'):
                st.markdown(f"**Expérience :** {job['experienceLibelle']}")
        
        with col2:
            if job.get('salaire') and job['salaire'].get('libelle'):
                st.markdown(f"**Salaire :** {job['salaire']['libelle']}")
        
        with col3:
            if job.get('posted_at'):
                st.markdown(f"**Publié le :** {job['posted_at']}")
        
        # Code ROME
        if job.get('romeCode'):
            st.markdown(f"**Code ROME :** {job['romeCode']}")
        
        # Description (si demandée)
        if show_full and job.get('description'):
            with st.expander("📄 Voir la description complète"):
                st.markdown(job['description'])
        
        # Compétences
        if job.get('competences') and len(job['competences']) > 0:
            with st.expander("🎯 Compétences requises"):
                comp_list = [f"- {comp.get('libelle', 'N/A')} ({comp.get('exigence', 'N/A')})" 
                            for comp in job['competences']]
                st.markdown("\n".join(comp_list))
        
        # Lien de candidature
        if job.get('apply_link'):
            st.markdown(f"[🔗 Postuler à cette offre]({job['apply_link']})")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_tension_indicator(tension_value: Optional[float]):
    """Affiche l'indicateur de tension du marché"""
    st.subheader("📊 Indicateur de Tension")
    if tension_value is not None:
        st.metric(
            label="Tension du marché",
            value=f"{tension_value:.2f}",
            help="Indicateur de tension entre offre et demande d'emploi"
        )
        
        # Interprétation
        if tension_value >= 4:
            st.info("🟢 Marché favorable aux candidats (plus d'offres que de demandes)")
        elif tension_value >= 2:
            st.warning("🟡 Marché équilibré")
        else:
            st.error("🔴 Marché tendu (plus de demandes que d'offres)")
    else:
        st.info("Données de tension non disponibles pour cette offre")


def display_equipment_radar(equipment_scores: Optional[Dict[str, Any]]):
    """Affiche le graphique radar des équipements du territoire"""
    st.subheader("🏘️ Équipements du Territoire")
    
    if equipment_scores:
        categories = [
            'Services particuliers',
            'Commerces',
            'Enseignement',
            'Santé & Action sociale',
            'Transports',
            'Sports & Loisirs',
            'Tourisme'
        ]
        
        values = [
            equipment_scores.get('services_particuliers', 0),
            equipment_scores.get('commerces', 0),
            equipment_scores.get('enseignement', 0),
            equipment_scores.get('sante_action_sociale', 0),
            equipment_scores.get('transports_deplacements', 0),
            equipment_scores.get('sports_loisirs_culture', 0),
            equipment_scores.get('tourisme', 0)
        ]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Scores'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Score total
        #total_score = equipment_scores.get('total', 0)
        #st.metric(
        #    label="Score total d'équipements",
        #    value=f"{total_score}/5",
        #    help="Note sur 5")
        
    else:
        st.info("Données d'équipements non disponibles pour ce département")

# ============== PAGE 1 : DASHBOARD STATISTIQUES ==============

# PAGE 1 : DASHBOARD STATISTIQUES
def page_dashboard():
    st.markdown('<p class="main-header">Projet Job Market</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">NOV25 Bootcamp DE</p>', unsafe_allow_html=True)
    
    # Vérification de l'API
    if not check_api_health():
        # Utilisez la variable dynamique ici pour ne plus être induit en erreur
        st.error(f"⚠️ L'API n'est pas accessible sur {API_BASE_URL}") 
        return
    
    st.success("✅ API connectée")
    
    # Métriques principales
    st.subheader("📈 Métriques Globales")
    
    total_data = get_total_jobs()
    
    if total_data:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Total des Offres",
                value=f"{total_data['total']:,}".replace(',', ' ')
            )
    
    st.divider()
    
    # Onglets pour les différentes visualisations
    tab1, tab2, tab3 = st.tabs(["🗺️ Par Département", "🌍 Par Région", "🎯 Compétences"])
    
    with tab1:
        st.subheader("Répartition des Offres par Département")
        
        dept_data = get_jobs_by_department(limit=100)
        
        if dept_data and dept_data.get('departments'):
            
            df_dept = pd.DataFrame(dept_data['departments'])
            df_dept = df_dept.sort_values('count', ascending=False)
            
            # Top 20 départements
            df_top20 = df_dept.head(20)
            
            col1, col2 = st.columns([2, 1])
            
            
            with col1:
                fig = px.bar(
                    df_top20,
                    y='lib_dep',
                    x='count',
                    orientation='h',
                    title='Répartition des Offres par département',
                    labels={'lib_dep': 'Département', 'count': 'Nombre d\'offres'},
                    color='count',
                    color_continuous_scale='Viridis',
                    text='count'
                )
                fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)


            
            with col2:
                st.markdown("### 🏆 Top 10")
                for idx, row in df_top20.head(10).iterrows():
                    lib_dep = row.get('lib_dep', row['code_dep'])
                    st.markdown(
                        f"**{row['code_dep']}** - {lib_dep}  \n"
                        f"📊 {row['count']:,} offres".replace(',', ' ')
                    )
            
            # Tableau complet
            with st.expander("📋 Voir tous les départements"):
                st.dataframe(
                    df_dept[['code_dep', 'lib_dep', 'count']].rename(columns={
                        'code_dep': 'Code',
                        'lib_dep': 'Département',
                        'count': 'Nombre d\'offres'
                    }),
                    use_container_width=True
                )
    
    with tab2:
        st.subheader("Répartition des Offres par Région")
        
        region_data = get_jobs_by_region(limit=100)
        
        if region_data and region_data.get('regions'):
            df_region = pd.DataFrame(region_data['regions'])
            df_region = df_region.sort_values('count', ascending=False)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.bar(
                    df_region,
                    y='lib_reg',
                    x='count',
                    orientation='h',
                    title='Répartition des Offres par Région',
                    labels={'lib_reg': 'Région', 'count': 'Nombre d\'offres'},
                    color='count',
                    color_continuous_scale='Viridis',
                    text='count'
                )
                fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 🏆 Top Régions")
                for idx, row in df_region.head(10).iterrows():
                    st.markdown(
                        f"**{row.get('lib_reg', row['code_reg'])}**  \n"
                        f"📊 {row['count']:,} offres".replace(',', ' ')
                    )
    
    with tab3:
        st.subheader("Compétences les Plus Demandées")
        
        limit_comp = st.slider("Nombre de compétences à afficher", 10, 100, 50)
        
        comp_data = get_top_competences(limit=limit_comp)
        
        if comp_data and comp_data.get('competences'):
            df_comp = pd.DataFrame(comp_data['competences'])
            
            # Top 20 en graphique
            df_top20_comp = df_comp.head(20)
            
            fig = px.bar(
                df_top20_comp,
                y='libelle',
                x='count',
                orientation='h',
                title='Top 20 des Compétences Demandées',
                labels={'libelle': 'Compétence', 'count': 'Nombre d\'offres'},
                color='count',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau complet
            with st.expander("📋 Voir toutes les compétences"):
                st.dataframe(
                    df_comp.rename(columns={
                        'libelle': 'Compétence',
                        'count': 'Nombre d\'offres'
                    }),
                    use_container_width=True
                )

# ============== PAGE 2 : RECHERCHE PAR DÉPARTEMENT ET PAR ID ==============

def page_search_jobs():
    st.markdown('<p class="main-header">Projet Job Market</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">NOV25 Bootcamp DE - Recherche d\'Offres</p>', unsafe_allow_html=True)
    
    # Vérification de l'API
    if not check_api_health():
        st.error("⚠️ L'API n'est pas accessible.")
        return
    
    # Création des onglets
    tab1, tab2 = st.tabs(["🗺️ Recherche par Département", "🔍 Recherche par ID"])
    
    # ========== ONGLET 1 : RECHERCHE PAR DÉPARTEMENT ==========
    with tab1:
        st.subheader("Recherche d'offres par département")
        
        # Sélection du département
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            code_dep = st.text_input(
                "Code du département",
                value="75",
                help="Entrez le code du département (ex: 75 pour Paris, 13 pour Bouches-du-Rhône)",
                key="dept_code"
            )
        
        with col2:
            limit = st.number_input(
                "Offres par page",
                min_value=1,
                max_value=100,
                value=10,
                key="dept_limit"
            )
        
        with col3:
            if 'dept_offset' not in st.session_state:
                st.session_state.dept_offset = 0
            
            page_number = st.number_input(
                "Page",
                min_value=1,
                value=(st.session_state.dept_offset // limit) + 1,
                key="dept_page"
            )
            st.session_state.dept_offset = (page_number - 1) * limit
        
        if st.button("🔍 Rechercher", type="primary", key="dept_search"):
            with st.spinner("Recherche en cours..."):
                results = get_jobs_by_dept_code(code_dep, limit, st.session_state.dept_offset)
                
                if results:
                    st.success(f"✅ {results['total']} offres trouvées pour le département {code_dep}")
                    
                    # Informations de pagination
                    st.info(
                        f"Affichage des offres {st.session_state.dept_offset + 1} "
                        f"à {min(st.session_state.dept_offset + limit, results['total'])} "
                        f"sur {results['total']}"
                    )
                    
                    # Affichage des offres
                    if results.get('items'):
                        for job in results['items']:
                            display_job_card(job, show_full=True)
                            st.divider()
                    else:
                        st.warning("Aucune offre sur cette page")
                else:
                    st.warning(f"Aucune offre trouvée pour le département {code_dep}")
    
    # ========== ONGLET 2 : RECHERCHE PAR ID ==========
    with tab2:
        st.subheader("Recherche d'offre par ID")
        st.info("💡 Recherchez une offre spécifique en utilisant son identifiant unique.")
        
        # Champ de saisie de l'ID
        job_id = st.text_input(
            "ID de l'offre",
            placeholder="Ex: 179BFLW",
            help="Entrez l'identifiant unique de l'offre d'emploi",
            key="job_id_input"
        )
        
        if st.button("🔍 Rechercher l'offre", type="primary", disabled=not job_id, key="id_search"):
            if job_id:
                with st.spinner("Recherche en cours..."):
                    job = get_job_by_id(job_id)
                    
                    if job:
                        st.success(f"✅ Offre trouvée avec l'ID : {job_id}")
                        
                        # Affichage de l'offre
                        display_job_card(job, show_full=True)
                    else:
                        st.warning(f"Aucune offre trouvée avec l'ID : {job_id}")


# ============== PAGE 3 : RECHERCHE SÉMANTIQUE ==============

def page_semantic_search():
    st.markdown('<p class="main-header">Projet Job Market</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">NOV25 Bootcamp DE - Recherche Sémantique</p>', unsafe_allow_html=True)
    
    # Vérification de l'API
    if not check_api_health():
        st.error("⚠️ L'API n'est pas accessible.")
        return
    
    st.info(
        "💡 Cette recherche utilise l'intelligence artificielle pour trouver les offres "
        "les plus pertinentes selon votre requête et votre localisation. "
        "Le filtre géographique est **obligatoire**."
    )
    
    # ========== SECTION 1 : PARAMÈTRES DE RECHERCHE ==========
    st.subheader("🔍 Paramètres de recherche")
    
    # Texte de recherche
    search_text = st.text_area(
        "Décrivez le poste recherché",
        placeholder="Ex: Data Engineer avec Python et SQL, expérience avec Spark et AWS...",
        help="Entrez une description détaillée du poste que vous recherchez",
        height=100
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        top_k = st.slider(
            "Nombre de résultats",
            min_value=1,
            max_value=50,
            value=10,
            help="Nombre d'offres les plus pertinentes à retourner"
        )
    
    with col2:
        geo_strategy = st.selectbox(
            "Stratégie géographique",
            options=["fallback", "strict"],
            index=0,
            help="fallback: élargit la zone si peu de résultats / strict: respecte exactement le filtre"
        )
    
    # ========== SECTION 2 : FILTRE GÉOGRAPHIQUE ==========
    st.subheader("📍 Filtre géographique (obligatoire)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        region_code = st.text_input(
            "Code région",
            placeholder="Ex: 11 (Île-de-France)",
            help="Code de la région (optionnel si département ou commune fourni)"
        )
    
    with col2:
        departement_code = st.text_input(
            "Code département",
            placeholder="Ex: 75 (Paris)",
            help="Code du département (optionnel si commune fournie)"
        )
    
    with col3:
        commune_code = st.text_input(
            "Code commune (INSEE)",
            placeholder="Ex: 75056 (Paris)",
            help="Code INSEE de la commune (le plus précis)"
        )
    
    # ========== SECTION 3 : LANCEMENT DE LA RECHERCHE ==========
    
    # Vérifier qu'au moins un filtre géo est fourni
    has_geo_filter = bool(region_code or departement_code or commune_code)
    
    if not has_geo_filter:
        st.warning("⚠️ Veuillez fournir au moins un filtre géographique (région, département ou commune)")
    
    if st.button(
        "🚀 Lancer la recherche sémantique",
        type="primary",
        disabled=not search_text or not has_geo_filter
    ):
        # Construire le filtre géographique
        geo_filter = {}
        if region_code:
            geo_filter['region_code'] = region_code
        if departement_code:
            geo_filter['departement_code'] = departement_code
        if commune_code:
            geo_filter['commune_code'] = commune_code
        
        with st.spinner("Recherche sémantique en cours..."):
            results = semantic_search(
                text=search_text,
                geo_filter=geo_filter,
                top_k=top_k,
                geo_strategy=geo_strategy
            )
            
            if results:
                st.success(f"✅ {len(results['items'])} offres trouvées !")
                
                # ========== INFORMATIONS SUR LA RECHERCHE ==========
                st.divider()
                st.subheader("ℹ️ Informations sur la recherche")
                
                info_col1, info_col2, info_col3 = st.columns(3)
                
                with info_col1:
                    st.metric("Résultats retournés", len(results['items']))
                    st.metric("Pool de candidats", results.get('candidate_pool', 'N/A'))
                
                with info_col2:
                    st.metric("Type de score", results.get('score_type', 'N/A'))
                    st.metric("Stratégie géo", results.get('geo_strategy', 'N/A'))
                
                with info_col3:
                    st.metric("Niveau géo appliqué", results.get('geo_applied_level', 'N/A'))
                    
                    geo_applied = results.get('geo_applied', {})
                    if geo_applied:
                        st.text("Filtre appliqué:")
                        for key, value in geo_applied.items():
                            st.text(f"  {key}: {value}")
                
                st.divider()
                
                # ========== AFFICHAGE DES RÉSULTATS ==========
                st.subheader("📋 Résultats de la recherche")
                
                for idx, item in enumerate(results['items'], 1):
                    st.markdown(f"### 🎯 Résultat #{idx}")
                    
                    job = item.get('job', {})
                    similarity_score = item.get('similarity_score')
                    tension_value = item.get('tension_value')
                    equipment_scores = item.get('equipment_scores')
                    
                    # Affichage de l'offre avec le score
                    display_job_card(job, show_full=True, similarity_score=similarity_score)
                    
                    # Affichage des indicateurs complémentaires
                    if tension_value is not None or equipment_scores:
                        with st.expander("📊 Voir les indicateurs du territoire"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                display_tension_indicator(tension_value)
                            
                            with col2:
                                display_equipment_radar(equipment_scores)
                    
                    st.divider()
            else:
                st.warning("Aucun résultat trouvé pour cette recherche.")


# ============== PAGE 4 : SIMILARITE COSINUS ==============
def page_similarity_comparison():
    st.markdown('<p class="main-header">Similarité Cosinus – Comparaison</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manual vs Native</p>', unsafe_allow_html=True)

    if not check_api_health():
        st.error("⚠️ L'API n'est pas accessible.")
        return

    # Texte d’entrée et Top K selectionnable
    input_text = st.text_input(
        "Texte de recherche",
        value="data engineer airflow"
    )

    top_k = st.slider("Top K", 1, 20, 10)

    if st.button("🧠 Lancer la comparaison", type="primary"):
        with st.spinner("Calcul des similarités..."):
            result = cosine_similarity_search(
                text=input_text,
                top_k=top_k
            )

        if not result:
            st.error("Aucun résultat retourné")
            return

        # ========================= INFOS GLOBALES (HAUT) =========================
        st.divider()
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Top K", result.get("top_k"))

        with col2:
            st.metric("Modèle", result.get("model_name"))

        with col3:
            st.metric("Same Top 1", "✅ Oui" if result["stats"]["same_top_1"] else "❌ Non")

        with col4:
            st.metric(
                "Native plus rapide",
                "⚡ Oui" if result["stats"]["native_is_faster"] else "🐢 Non"
            )

        st.info(f"📝 **Texte analysé :** `{result.get('input_text')}`")

        # ========================= STATS D’EXÉCUTION =========================
        st.subheader("📊 Statistiques de calcul")

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Manual – Temps (ms)",
                f"{result['stats']['execution_time_ms_manual']:.2f}"
            )

        with col2:
            st.metric(
                "Native – Temps (ms)",
                f"{result['stats']['execution_time_ms_native']:.2f}"
            )

        # ========================= COMPARAISON CÔTE À CÔTE =========================
        st.divider()
        st.subheader("🆚 Comparaison des résultats")

        manual_items, native_items = split_similarity_results(result["items"])

        col_manual, col_native = st.columns(2)

        # -------- MANUAL --------
        with col_manual:
            st.markdown("## 🧮 Manual")
            for item in manual_items:
                job = item["job"]
                st.markdown(
                    f"""
                    **#{item['rank']} – Score : {item['similarity_score']:.4f}**  
                    **{job['title']}**  
                    🏢 {job['employer']}  
                    📍 {job['location']}  
                    """
                )
                with st.expander("📄 Description"):
                    st.write(job["description"])

        # -------- NATIVE --------
        with col_native:
            st.markdown("## ⚡ Native")
            for item in native_items:
                job = item["job"]
                st.markdown(
                    f"""
                    **#{item['rank']} – Score : {item['similarity_score']:.4f}**  
                    **{job['title']}**  
                    🏢 {job['employer']}  
                    📍 {job['location']}  
                    """
                )
                with st.expander("📄 Description"):
                    st.write(job["description"])

# ============== NAVIGATION ==============

def main():
    # Sidebar
    # Logo en haut de la sidebar
    BASE_DIR = Path(__file__).resolve().parent
    logo_path = BASE_DIR / "logo.png"
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=200)
    else:
        st.sidebar.warning(f"Logo non trouvé : {logo_path}")
    
    st.sidebar.title("🧭 Navigation")
    
    page = st.sidebar.radio(
        "Choisissez une page",
        ["📊 Dashboard", "🗺️ Récupération Offres brutes", "🔎 Recherche Sémantique", "🧠 Similarité – Manual vs Native"]
    )
    
    st.sidebar.divider()
    
    # Informations sur l'API
    st.sidebar.subheader("ℹ️ Informations")
    st.sidebar.text(f"API : {API_BASE_URL}")
    
    if check_api_health():
        st.sidebar.success("✅ API connectée")
    else:
        st.sidebar.error("❌ API déconnectée")
    
    st.sidebar.divider()
    
    # À propos
    st.sidebar.subheader("📖 À propos")
    st.sidebar.info(
        "**Projet Job Market**  \n"
        "NOV25 Bootcamp DE  \n\n"
        "Application d'exploration du marché de l'emploi en France "
        "avec statistiques détaillées, recherche par département, par ID, "
        "recherche sémantique IA, indicateurs de tension et scores d'équipements des territoires."
    )
    
    # Affichage de la page sélectionnée
    if page == "📊 Dashboard":
        page_dashboard()
    elif page == "🗺️ Récupération Offres brutes":
        page_search_jobs()
    elif page == "🔎 Recherche Sémantique":
        page_semantic_search()
    elif page == "🧠 Similarité – Manual vs Native":
        page_similarity_comparison()

if __name__ == "__main__":
    main()
