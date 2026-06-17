import json
import os
from pathlib import Path
from datetime import datetime

def save_json(data, output_dir, filename):
    """
    Sauvegarde JSON avec timestamp.
    
    Args:
        data: Données à sauvegarder
        output_dir: Répertoire de sortie (Path)
        filename: Nom du fichier (sans extension)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = output_dir / f"{filename}_{timestamp}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath

def deduplicate(data, key):
    """
    Dédoublonne par clé.
    
    Args:
        data: Liste de dictionnaires
        key: Clé pour identifier doublons
    """
    unique = {item[key]: item for item in data}
    return list(unique.values())

def load_json(filepath):
    """
    Charge JSON ou JSONL (compatible Adzuna/FT).
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            # Essai JSON unique (array/dict)
            return json.load(f)
        except json.JSONDecodeError as e:
            if "Extra data" in str(e):
                # JSONL détecté : rewind et parse ligne par ligne
                f.seek(0)
                data = []
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError as line_e:
                            print(f"Erreur ligne {line_num}: {line_e}")
                            continue  # Skip ligne corrompue
                print(f"Chargé {len(data)} objets depuis JSONL {filepath}")
                return data
            raise  # Autre erreur

def load_latest_json(directory, pattern="*.json"):
    """Inchangé sauf appel à nouveau load_json."""
    directory = Path(directory)
    json_files = list(directory.glob(pattern))
    if not json_files:
        return None, None
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    data = load_json(latest_file)  # Auto-détecte JSON/JSONL
    return data, latest_file

