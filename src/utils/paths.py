"""
Chemins du projet.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Données brutes
DATA_RAW_FT = PROJECT_ROOT / "data/raw/france_travail"
DATA_RAW_ADZUNA = PROJECT_ROOT / "data/raw/adzuna"
DATA_RAW_JSEARCH = PROJECT_ROOT / "data/raw/jsearch"
DATA_RAW_INSEE_EQPT = PROJECT_ROOT / "data/raw/insee_eqpt"
DATA_RAW_DATAGOUV = PROJECT_ROOT / "data/raw/data_gouv" 


# Données transformées
DATA_PRO_FT = PROJECT_ROOT / "data/processed/france_travail"
DATA_PRO_ADZUNA = PROJECT_ROOT / "data/processed/adzuna"
DATA_PRO_JSEARCH = PROJECT_ROOT / "data/processed/jsearch"
DATA_PRO_INSEE_EQPT = PROJECT_ROOT / "data/processed/insee_eqpt"
DATA_PRO_UNIFIED = PROJECT_ROOT / "data/processed/unified"

# Création automatique des répertoires
for directory in [
    DATA_RAW_FT,
    DATA_RAW_ADZUNA,
    DATA_RAW_JSEARCH,
    DATA_RAW_DATAGOUV, 
    DATA_RAW_INSEE_EQPT,
    DATA_PRO_FT,
    DATA_PRO_ADZUNA,
    DATA_PRO_JSEARCH,
    DATA_PRO_INSEE_EQPT
]:
    directory.mkdir(parents=True, exist_ok=True)
