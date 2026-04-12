"""
cache_ressources.py — Couche cache Streamlit pour tstat_analyse.

Rôle :
    1. Bootstrap des singletons dans le processus Streamlit (_bootstrap)
    2. toutes les ressources globales (instances, fonctions d'accès aux données) utilisées par les pages.    
        si des ressosurces doivent être réinitialisées des fonctions explcites de réinitialisations seront ajoutées.

Pourquoi _bootstrap() ici ?
    Streamlit tourne dans un subprocess séparé du lanceur.
    Les singletons (clsINICommun, clsLOG, clsDBAManager...) initialisés
    dans run_tstat_analyse.py n'existent pas dans ce processus.
    _bootstrap() les réinitialise une seule fois via st.cache_resource.
    Toutes les valeurs nécessaires (chemins, constantes) sont transmises
    par run_tstat_analyse.py via os.environ — zéro duplication.
"""

import os
import streamlit as st

_TTL = 300


# =============================================================================
# Bootstrap — une seule fois par session serveur
# =============================================================================

@st.cache_resource
def bootstrap() -> None:
    """
    Initialise les singletons du framework dans le processus Streamlit.
    Les constantes projet sont lues depuis os.environ — calculées une
    seule fois dans run_tstat_analyse.py, transmises via le subprocess.
    """
    from pathlib import Path
    from sysclasses.cste_chemins import init_chemins
    from sysclasses.AppBootstrap import AppBootstrap
    from projets.tstat_analyse.clsINITstatAnalyse import clsINITstatAnalyse

    init_chemins(
        Path(os.environ["TSTAT_PROJET_RACINE"]),
        os.environ["TSTAT_PROJET_NOM"],
        os.environ["TSTAT_PROJET_VER"],
    )
    AppBootstrap(os.environ["TSTAT_INI_FILE"], clsINITstatAnalyse, mode='streamlit')