"""
cache_charge.py — Couche cache Streamlit pour tstat_analyse et les fonctions et méthodes liées à la recharge du véhicule.

Rôle :
    Gérer les données en fonction de la durée de vie du TTL et de la logique métier de la recharge.

TTL par défaut : 300s (5 minutes) — cohérent avec le cycle de collecte.
"""

import os
import streamlit as st
from projets.tstat_analyse.clsTstatCharge import clsTstatCharge
from cache_ressources import get_charge

_TTL = 300


# =============================================================================
# Référentiel véhicules
# =============================================================================

@st.cache_data(ttl=_TTL)
def get_liste_vehicules() -> list[dict]:
    """
    Liste des véhicules actifs (veh_id + veh_displayname), triés alphabétiquement.
    Source : TSTAT_ADMIN — t_vehicle_veh.
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
def get_kpi_home(veh_id: int = None) -> dict:
    """Tous les KPI scalaires de la page d'accueil."""
    return get_charge().kpi_home(veh_id=veh_id)


@st.cache_data(ttl=_TTL)
def get_energie_par_jour(veh_id: int = None, nb_jours: int = 30) -> list[dict]:
    """
    Énergie ajoutée par jour sur les nb_jours derniers jours.
    Source : mv_charge_journee — une ligne par jour (pas d'agrégation session).
    Utilisé pour le mini-graphique de la home.
    """
    from datetime import date, timedelta
    date_debut = (date.today() - timedelta(days=nb_jours)).isoformat()
    return get_charge().energie_par_jour(
        veh_id     = veh_id,
        date_debut = date_debut,
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