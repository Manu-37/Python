"""
cache_charge.py — Couche cache Streamlit pour tstat_analyse.

Rôle :
    Mettre en cache les appels aux contrôleurs et aux classes Q.
    TTL par défaut : 300s (5 minutes) — cohérent avec le cycle de collecte.
"""

import streamlit as st
from projets.tstat_analyse import kpi_home, serie_energie_par_jour
from db.db_tstat_data import clsQ_charge_sessions_ext

_TTL = 300


# =============================================================================
# Référentiel véhicules
# =============================================================================

@st.cache_data(ttl=_TTL)
def get_liste_vehicules() -> list[dict]:
    """
    Liste des véhicules actifs (veh_id + veh_displayname), triés alphabétiquement.
    Source : TSTAT_DATA — t_vehicle_veh.
    """
    from sysclasses.clsDBAManager import clsDBAManager
    engine = clsDBAManager().get_db("TSTAT_DATA")
    rows   = engine.execute_select(
        "SELECT veh_id, veh_displayname "
        "FROM public.t_vehicle_veh "
        "WHERE veh_isactive = TRUE "
        "ORDER BY veh_displayname ASC"
    )
    return rows or []


# =============================================================================
# KPI home
# =============================================================================

@st.cache_data(ttl=_TTL)
def get_kpi_home(veh_id: int) -> dict:
    """Tous les KPI scalaires de la page d'accueil."""
    return kpi_home(veh_id)


@st.cache_data(ttl=_TTL)
def get_energie_par_jour(veh_id: int, nb_jours: int = 30) -> list[dict]:
    """
    Énergie ajoutée et kilométrage par jour sur les nb_jours derniers jours.
    Source : mv_journee — couvre tous les jours avec snapshots.
    Utilisé pour le mini-graphique de la home.
    """
    from datetime import date, timedelta
    date_debut = (date.today() - timedelta(days=nb_jours)).isoformat()
    return serie_energie_par_jour(veh_id=veh_id, date_debut=date_debut)


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
    return clsQ_charge_sessions_ext().sessions_par_periode(
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
    return clsQ_charge_sessions_ext().capacite_par_periode(
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
    return clsQ_charge_sessions_ext().kilometrage_par_periode(
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
    return clsQ_charge_sessions_ext().sessions_recentes(veh_id=veh_id, limite=limite)
