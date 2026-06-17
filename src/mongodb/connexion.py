"""
Gestion de la connexion MongoDB.
"""
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from .config import MONGO_CONFIG

logger = logging.getLogger(__name__)

def get_mongo_client() -> MongoClient:
    """
    Établit une connexion à MongoDB.
    
    Returns:
        MongoClient: Client MongoDB connecté
    """
    try:
        client = MongoClient(
            host=MONGO_CONFIG["host"],
            port=MONGO_CONFIG["port"],
            username=MONGO_CONFIG["username"],
            password=MONGO_CONFIG["password"]
        )
        
        client.admin.command('ping')
        logger.info(f"Connexion MongoDB : {MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}")
        
        return client
        
    except ConnectionFailure as e:
        logger.error(f"Erreur connexion MongoDB : {e}")
        raise

def get_database(db_name: str = None):
    """
    Retourne une instance de base de données MongoDB.
    
    Args:
        db_name: Nom de la base (défaut: MONGO_CONFIG["database"])
    """
    client = get_mongo_client()
    db_name = db_name or MONGO_CONFIG["database"]
    return client[db_name]

def check_mongodb_connection(db_name: str = "job_market"):
    """
    Vérifie la connexion à MongoDB.

    :param db_name: Nom de la base MongoDB
    :return: Objet DB ou None si échec
    """
    try:
        db = get_database(db_name)
        logger.info(f"Connexion réussie à MongoDB : {db_name}")
        return db

    except ConnectionFailure as e:
        logger.error(f"Impossible de se connecter à MongoDB : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la connexion à MongoDB : {e}")

    return None

def list_existing_collections(db):
    """
    Liste les collections existantes dans la base MongoDB.

    :param db: Objet MongoDB
    :return: Liste des collections
    """
    if db is None:
        logger.error("DB est None, impossible de lister les collections")
        return []

    try:
        collections = db.list_collection_names()

        if collections:
            logger.info("Collections disponibles :")
            for col in collections:
                logger.info(f" - {col}")
        else:
            logger.warning("Aucune collection trouvée dans la base")

        return collections

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des collections : {e}")
        return []

def check_collection_exist(db, collection_name: str) -> bool:
    """
    Vérifie si la collection existe dans la DB.
    
    :param db: Objet MongoDB
    :param collection_name: Nom de la collection
    :return: True si existe, False sinon
    """
    if db is None:
        logger.error("Database is None")
        return False
    try:
        if collection_name in db.list_collection_names():
            logger.info(f"La collection '{collection_name}' existe dans la DB.")
            return True
        else:
            logger.warning(f"La collection '{collection_name}' n'existe pas dans la DB.")
            return False
    except PyMongoError as e:
        logger.error(f"Erreur lors de la vérification de la collection : {e}")
        return False