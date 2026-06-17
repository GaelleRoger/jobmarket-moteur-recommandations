"""
Mapping des codes arrondissements vers communes de rattachement
Utilisé pour harmoniser les données géographiques des 3 sources (France Travail, Adzuna, JSearch)
"""

# Mapping arrondissements → commune de rattachement
ARRONDISSEMENTS_TO_COMMUNE = {
    # Paris (75) - 20 arrondissements
    '75101': '75056', '75102': '75056', '75103': '75056', '75104': '75056',
    '75105': '75056', '75106': '75056', '75107': '75056', '75108': '75056',
    '75109': '75056', '75110': '75056', '75111': '75056', '75112': '75056',
    '75113': '75056', '75114': '75056', '75115': '75056', '75116': '75056',
    '75117': '75056', '75118': '75056', '75119': '75056', '75120': '75056',
    
    # Lyon (69) - 9 arrondissements
    '69381': '69123', '69382': '69123', '69383': '69123', '69384': '69123',
    '69385': '69123', '69386': '69123', '69387': '69123', '69388': '69123',
    '69389': '69123',
    
    # Marseille (13) - 16 arrondissements
    '13201': '13055', '13202': '13055', '13203': '13055', '13204': '13055',
    '13205': '13055', '13206': '13055', '13207': '13055', '13208': '13055',
    '13209': '13055', '13210': '13055', '13211': '13055', '13212': '13055',
    '13213': '13055', '13214': '13055', '13215': '13055', '13216': '13055',
}


def get_commune_rattachement(code_com: str) -> str:
    """
    Retourne le code commune de rattachement si le code fourni est un arrondissement,
    sinon retourne le code inchangé.
    
    Args:
        code_com: Code commune ou arrondissement (ex: '75101' ou '69001')
        
    Returns:
        Code commune de rattachement (ex: '75056' pour Paris, '69123' pour Lyon)
        ou code inchangé si ce n'est pas un arrondissement
        
    Examples:
        >>> get_commune_rattachement('75101')
        '75056'
        >>> get_commune_rattachement('69001')
        '69001'
        >>> get_commune_rattachement('13208')
        '13055'
    """
    return ARRONDISSEMENTS_TO_COMMUNE.get(code_com, code_com)


def is_arrondissement(code_com: str) -> bool:
    """
    Vérifie si un code commune est un arrondissement.
    
    Args:
        code_com: Code commune à vérifier
        
    Returns:
        True si c'est un arrondissement, False sinon
        
    Examples:
        >>> is_arrondissement('75101')
        True
        >>> is_arrondissement('75056')
        False
    """
    return code_com in ARRONDISSEMENTS_TO_COMMUNE


def get_arrondissements_by_commune(code_com: str) -> list:
    """
    Retourne la liste des codes arrondissements pour une commune donnée.
    
    Args:
        code_com: Code commune (ex: '75056' pour Paris)
        
    Returns:
        Liste des codes arrondissements de cette commune
        
    Examples:
        >>> len(get_arrondissements_by_commune('75056'))
        20
        >>> len(get_arrondissements_by_commune('69123'))
        9
    """
    return [arr for arr, com in ARRONDISSEMENTS_TO_COMMUNE.items() if com == code_com]


# Métadonnées pour documentation
COMMUNES_WITH_ARRONDISSEMENTS = {
    '75056': {'nom': 'Paris', 'nb_arrondissements': 20},
    '69123': {'nom': 'Lyon', 'nb_arrondissements': 9},
    '13055': {'nom': 'Marseille', 'nb_arrondissements': 16},
}

