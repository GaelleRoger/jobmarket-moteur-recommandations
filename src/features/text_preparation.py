import re

def clean_text(text: str) -> str:
    """Nettoyage minimal du texte pour embeddings."""
    # Remplacer les sauts de ligne et tabulations par des espaces
    text = re.sub(r'[\n\r\t]+', ' ', text)
    
    # Supprimer les espaces multiples
    text = ' '.join(text.split())
    
    return text.strip()

def build_composite_text(offer: dict) -> str:
    """Construit un texte composite pour l'embedding à partir d'une offre."""
    parts = []
    
    title = offer.get('title', '').strip()
    if title:
        parts.append(title)
    
    description = offer.get('description', '').strip()
    if description:
        parts.append(description)
    
    employer = offer.get('employer') or ''  
    employer = employer.strip()
    if employer:
        parts.append(f"Entreprise: {employer}")
    
    competences = offer.get('competences')
    if competences and isinstance(competences, list):
        libelles = [
            comp.get('libelle', '').strip() 
            for comp in competences 
            if isinstance(comp, dict) and comp.get('libelle')
        ]
        if libelles:
            parts.append(f"Compétences: {', '.join(libelles)}")
    
    composite_text = '. '.join(parts)
    
    # Nettoyage final
    composite_text = clean_text(composite_text)
    
    return composite_text
