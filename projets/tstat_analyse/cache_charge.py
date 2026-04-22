"""
cache_charge.py — Couche cache Streamlit pour tstat_analyse.

Rôle :
    Mettre en cache les appels aux contrôleurs et aux classes Q.
    TTL par défaut : 300s (5 minutes) — cohérent avec le cycle de collecte.
"""

import streamlit as st
from datetime import date, timedelta
from projets.tstat_analyse import kpi_home, serie_energie_par_jour, serie_capacite_glissante, serie_energie_par_periode, serie_sessions, courbe_session

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
    date_debut = (date.today() - timedelta(days=nb_jours+1)).isoformat()
    date_fin   = (date.today() - timedelta(days=1)).isoformat()  # on prend la journée d'hier, la plus récente complète   
    return serie_energie_par_jour(veh_id=veh_id, date_debut=date_debut, date_fin=date_fin)


# =============================================================================
# Données page charge
# =============================================================================


@st.cache_data(ttl=_TTL)
def get_capacite_glissante(
    veh_id    : int,
    nb_points : int,
    duree     : str,
    date_fin,
) -> list[dict]:
    """Capacité et moyenne glissante par jour. Source : mv_journee via ctrl_charge."""
    return serie_capacite_glissante(veh_id, nb_points, duree, date_fin)

@st.cache_data(ttl=_TTL)
def get_energie_par_periode(veh_id:int, duree:str, date_fin:date, date_comparaison:date) -> dict[int,list[dict]]:
    """
    Énergie ajoutée et kilométrage par jour sur les nb_jours derniers jours.
    Source : mv_journee — couvre tous les jours avec snapshots.
    Utilisé pour le mini-graphique de la home.
    """
    return serie_energie_par_periode(veh_id=veh_id, duree=duree, date_fin=date_fin, date_comparaison=date_comparaison)

@st.cache_data(ttl=_TTL)
def get_sessions(veh_id: int, duree: str, date_fin: date) -> list[dict]:
    """Sessions brutes sur la période. Source : mv_charge_sessions_ext via ctrl_charge."""
    return serie_sessions(veh_id=veh_id, duree=duree, date_fin=date_fin)

@st.cache_data(ttl=_TTL)
def get_courbe_session(snp_id_debut: int, snp_id_fin: int) -> list[dict]:
    """Points de charge bruts pour une session. Source : t_snapshot_snp + t_charge_chg."""
    return courbe_session(snp_id_debut=snp_id_debut, snp_id_fin=snp_id_fin)