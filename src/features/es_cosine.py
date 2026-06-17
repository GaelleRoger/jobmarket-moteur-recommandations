from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

class JobSearchEngine:
    def __init__(self, es_host='http://localhost:9200'):
        """Initialise le moteur de recherche"""
        self.es = Elasticsearch([es_host])
        # IMPORTANT: Utiliser le même modèle que pour l'indexation
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print(f"Modèle chargé: paraphrase-multilingual-MiniLM-L12-v2 (384 dims)")
        
    def search_by_similarity(self, query_text, top_k=10):
        """
        Recherche par similarité cosinus
        
        Args:
            query_text (str): Texte de recherche
            top_k (int): Nombre de résultats
        
        Returns:
            list: Liste des offres avec scores
        """
        # Générer l'embedding de la requête
        print(f"Génération de l'embedding pour: '{query_text}'")
        query_embedding = self.model.encode(query_text).tolist()
        print(f"Embedding généré ({len(query_embedding)} dimensions)")
        
        # Construction du knn
        knn_query = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 10
        }
        
        # Exécuter la recherche
        response = self.es.search(
            index='offres_unified',
            knn=knn_query,
            source_excludes=["embedding"]
        )
        
        return response['hits']['hits']
    
    def search_hybrid(self, query_text, top_k=10, text_boost=0.3, vector_boost=0.7):
        """
        Recherche hybride : combinaison de recherche textuelle et vectorielle
        
        Args:
            query_text (str): Texte de recherche
            top_k (int): Nombre de résultats
            text_boost (float): Poids de la recherche textuelle (0-1)
            vector_boost (float): Poids de la recherche vectorielle (0-1)
        """
        query_embedding = self.model.encode(query_text).tolist()
        
        # Construction de la requête bool
        bool_query = {
            "should": [
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["title^3", "description", "employer"],
                        "boost": text_boost
                    }
                }
            ]
        }
        
        # Construction du knn
        knn_query = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 10,
            "boost": vector_boost
        }
        
        # SYNTAXE ELASTICSEARCH 8.x
        response = self.es.search(
            index='offres_unified',
            query={"bool": bool_query},
            knn=knn_query,
            size=top_k,
            source_excludes=["embedding"]
        )
        
        return response['hits']['hits']
    
    def display_results(self, results, show_description=True):
        """Affiche les résultats de manière formatée"""
        if not results:
            print("Aucun résultat trouvé")
            return
            
        print(f"\n{'='*100}")
        print(f"Trouvé {len(results)} offres\n")
        
        for i, hit in enumerate(results, 1):
            source = hit['_source']
            score = hit['_score']
            
            print(f"{i}. SCORE DE SIMILARITÉ: {score:.4f}")
            print(f"Titre: {source.get('title', 'N/A')}")
            print(f"Entreprise: {source.get('employer', 'N/A')}")
            print(f"Lieu: {source.get('location', 'N/A')}")
            
            if source.get('lieuTravail'):
                lieu = source['lieuTravail']
                print(f"      → Région: {lieu.get('libReg', 'N/A')}, "
                      f"Département: {lieu.get('libDep', 'N/A')}, "
                      f"Code Postal: {lieu.get('codePostal', 'N/A')}")
            
            if source.get('posted_at'):
                print(f"Publié le: {source['posted_at']}")
            
            if source.get('source'):
                print(f"Source: {source['source']}")
            
            print(f"Postuler: {source.get('apply_link', 'N/A')}")
            
            if show_description and source.get('description'):
                desc = source['description']
                # Tronquer à 250 caractères
                desc_short = desc[:250] + "..." if len(desc) > 250 else desc
                print(f"Description: {desc_short}")
            
            print(f"   {'─'*96}\n")

if __name__ == "__main__":
    # Initialiser le moteur
    print("🚀 Initialisation du moteur de recherche...")
    engine = JobSearchEngine()
    
    print("\n" + "="*100)
    print("Recherche simple par similarité")
    print("="*100)
    query1 = "Data engineer spécialisé Docker, Snowflake et Kubernetes"
    results1 = engine.search_by_similarity(query1, top_k=5)
    engine.display_results(results1, show_description=False)