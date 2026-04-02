"""
cache.py — Couche cache Streamlit pour tstat_analyse.

Rôle :
    1. Bootstrap des singletons dans le processus Streamlit (_bootstrap)
    2. Isolation de toute dépendance st.cache_* dans un seul fichier

Pourquoi _bootstrap() ici ?
    Streamlit tourne dans un subprocess séparé du lanceur.
    Les singletons (clsINICommun, clsLOG, clsDBAManager...) initialisés
    dans run_tstat_analyse.py n'existent pas dans ce processus.
    _bootstrap() les réinitialise une seule fois via st.cache_resource.
    Toutes les valeurs nécessaires (chemins, constantes) sont transmises
    par run_tstat_analyse.py via os.environ — zéro duplication.

TTL par défaut : 300s (5 minutes) — cohérent avec le cycle de collecte.
"""

import os
import streamlit as st
from projets.tstat_analyse.clsTstatCharge import clsTstatCharge

_TTL = 300


# =============================================================================
# Bootstrap — une seule fois par session serveur
# =============================================================================

@st.cache_resource
def _bootstrap() -> None:
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


# =============================================================================
# Singleton clsTstatCharge — une seule instance par session serveur
# =============================================================================

@st.cache_resource
def get_charge() -> clsTstatCharge:
    """
    Retourne l'instance unique de clsTstatCharge pour la session serveur.
    _bootstrap() est appelé en premier — garantit que les singletons
    du framework existent avant d'instancier clsTstatCharge.
    """
    _bootstrap()
    return clsTstatCharge()


# =============================================================================
# KPI home
# =============================================================================

@st.cache_data(ttl=_TTL)
def get_kpi_home(veh_id: int = None) -> dict:
    """Tous les KPI scalaires de la page d'accueil."""
    return get_charge().kpi_home(veh_id=veh_id)


@st.cache_data(ttl=_TTL)
def get_energie_par_jour(veh_id: int = None, nb_jours: int = 30) -> list[dict]:
    """
    Énergie ajoutée par jour sur les nb_jours derniers jours.
    Utilisé pour le mini-graphique de la home.
    """
    from datetime import date, timedelta
    date_debut = (date.today() - timedelta(days=nb_jours)).isoformat()
    return get_charge().sessions_par_periode(
        granularite = "jour",
        veh_id      = veh_id,
        date_debut  = date_debut,
    )


# =============================================================================
# Données page charge
# =============================================================================

@st.cache_data(ttl=_TTL)
def get_sessions_par_periode(
    granularite : str  = "mois",
    veh_id      : int  = None,
    date_debut  : str  = None,
    date_fin    : str  = None,
    etat_final  : str  = None,
) -> list[dict]:
    return get_charge().sessions_par_periode(
        granularite = granularite,
        veh_id      = veh_id,
        date_debut  = date_debut,
        date_fin    = date_fin,
        etat_final  = etat_final,
    )


@st.cache_data(ttl=_TTL)
def get_capacite_par_periode(
    granularite : str = "mois",
    veh_id      : int = None,
    date_debut  : str = None,
    date_fin    : str = None,
) -> list[dict]:
    return get_charge().capacite_par_periode(
        granularite = granularite,
        veh_id      = veh_id,
        date_debut  = date_debut,
        date_fin    = date_fin,
    )


@st.cache_data(ttl=_TTL)
def get_kilometrage_par_periode(
    granularite : str = "mois",
    veh_id      : int = None,
    date_debut  : str = None,
    date_fin    : str = None,
) -> list[dict]:
    return get_charge().kilometrage_par_periode(
        granularite = granularite,
        veh_id      = veh_id,
        date_debut  = date_debut,
        date_fin    = date_fin,
    )


@st.cache_data(ttl=_TTL)
def get_sessions_recentes(
    veh_id : int = None,
    limite : int = 50,
) -> list[dict]:
    return get_charge().sessions_recentes(veh_id=veh_id, limite=limite)