"""
widgets.py — Composants Streamlit réutilisables.

Chaque fonction encapsule un bloc visuel complet (colonnes + contenu).
Aucune logique métier, aucun appel DB.
"""

import streamlit as st
from utilis import COULEURS, fmt_float, km_par_kwh, kpi_bloc_format


def ligne_kpi(label: str, km: float, energie: float, conso: float):
    """
    Affiche une ligne de KPI : label | km | énergie | consommation | rendement.
    Réutilisable sur accueil (mois/année) et charge (sélection courante).
    """
    col_label, col_km, col_nrj, col_conso, col_rendement, _, _ = st.columns(7)
    with col_label:
        st.markdown(f"**{label}**")
    with col_km:
        st.markdown(kpi_bloc_format(fmt_float(km,      decimales=0, suffixe=" km"),        COULEURS["km"]),        unsafe_allow_html=True)
    with col_nrj:
        st.markdown(kpi_bloc_format(fmt_float(energie, decimales=1, suffixe=" kWh"),       COULEURS["energie"]),   unsafe_allow_html=True)
    with col_conso:
        st.markdown(kpi_bloc_format(fmt_float(conso,   decimales=1, suffixe=" kWh/100km"), COULEURS["conso"]),     unsafe_allow_html=True)
    with col_rendement:
        st.markdown(kpi_bloc_format(fmt_float(km_par_kwh(km, energie), decimales=1, suffixe=" km/kWh"), COULEURS["rendementk"]), unsafe_allow_html=True)


def entete_tableau_kpi():
    """En-têtes des colonnes du tableau KPI."""
    _, col_km, col_nrj, col_conso, col_rendement, _, _ = st.columns(7)
    with col_km:        st.markdown("**Kilométrage**")
    with col_nrj:       st.markdown("**Énergie rechargée**")
    with col_conso:     st.markdown("**Consommation**")
    with col_rendement: st.markdown("**Rendement kilométrique**")
