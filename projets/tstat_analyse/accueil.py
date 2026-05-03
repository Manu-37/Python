"""
accueil.py — Page d'accueil du dashboard tstat_analyse.

Disposition :
    Sélecteur véhicule — titre
    ─────────────────────────────────────────────────────────────────
    État courant (7 colonnes) :
        Dernière charge | Km jour | Énergie jour | Conso jour |
        Rendement km | Moyenne 7j capacité | Dernière estimation capacité
    ─────────────────────────────────────────────────────────────────
    Tableau kilométrage / énergie / consommation / rendement — mois et année
    ─────────────────────────────────────────────────────────────────
    Graphique énergie par jour — 30 derniers jours

Orchestrateur pur — pas de logique métier ni de calcul.
Toutes les données viennent de cache_charge.py.
"""

import streamlit as st
from cache_ressources import bootstrap
from cache_charge import get_kpi_home, get_energie_par_jour, get_liste_vehicules
from utilis import COULEURS, fmt_float, km_par_kwh, kpi_bloc_format, delta_couleur, delta_texte
from charts import fig_energie_km
from widgets import ligne_kpi, entete_tableau_kpi

# =============================================================================
# Bootstrap — obligatoire avant tout appel cache
# =============================================================================

bootstrap()

# =============================================================================
# Configuration de la page
# =============================================================================

st.set_page_config(
    page_title = "tstat — Accueil",
    page_icon  = "⚡",
    layout     = "wide",
)

# =============================================================================
# Titre + sélecteur véhicule
# =============================================================================

vehicules = get_liste_vehicules()

col_titre, col_combo = st.columns([4, 1])
with col_titre:
    st.title("⚡ Tesla Stats — Tableau de bord")
with col_combo:
    st.write("")
    if vehicules:
        noms   = [v["veh_displayname"] for v in vehicules]
        ids    = [v["veh_id"]          for v in vehicules]
        choix  = st.selectbox("", noms, index=0, label_visibility="collapsed")
        VEH_ID = ids[noms.index(choix)]
    else:
        st.caption("Aucun véhicule")
        VEH_ID = None

NB_JOURS = 30

# =============================================================================
# Chargement des données
# =============================================================================

kpi               = get_kpi_home(veh_id=VEH_ID)
serie             = get_energie_par_jour(veh_id=VEH_ID, nb_jours=NB_JOURS)
derniere          = kpi.get("derniere_session")  or {}
derniere_recharge = kpi.get("derniere_recharge") or {}

# =============================================================================
# État courant — 7 colonnes
# Ordre : Dernière charge | Km jour | Énergie | Conso | Rendement | Cap. moy 7j | Cap. dernière
# =============================================================================

st.divider()
st.subheader("État courant")

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    debut = derniere.get("debut_session")
    st.markdown(
        kpi_bloc_format(
            valeur = debut.strftime("%d/%m/%Y") if debut else "—",
            label  = "Dernière charge",
        ),
        unsafe_allow_html=True,
    )

with col2:
    date_prec = derniere_recharge.get("date_recharge_precedente")
    label_prec = date_prec.strftime("%d/%m/%Y") if date_prec else "—"
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(derniere_recharge.get("km_depuis_charge_precedente"), decimales=0, suffixe=" km"),
            couleur = COULEURS["km"],
            label   = f"Km depuis recharge — {label_prec}",
        ),
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(derniere_recharge.get("energie_ajoutee_kwh"), decimales=1, suffixe=" kWh"),
            couleur = COULEURS["energie"],
            label   = "Énergie rechargée",
        ),
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(derniere_recharge.get("conso_kwh_100km"), decimales=1, suffixe=" kWh/100km"),
            couleur = COULEURS["conso"],
            label   = "Consommation",
        ),
        unsafe_allow_html=True,
    )

with col5:
    km  = derniere_recharge.get("km_depuis_charge_precedente")
    kwh = derniere_recharge.get("energie_ajoutee_kwh")
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(km_par_kwh(km, kwh), decimales=1, suffixe=" km/kWh"),
            couleur = COULEURS["rendementk"],
            label   = "Rendement kilométrique",
        ),
        unsafe_allow_html=True,
    )

with col6:
    cap_derniere   = kpi.get("derniere_capacite")
    cap_precedente = derniere.get("capacite_estimee_kwh")
    delta_cap = None
    if cap_derniere is not None and cap_precedente is not None:
        try:
            delta_cap = round(float(cap_derniere) - float(cap_precedente), 1)
        except Exception:
            pass
    st.markdown(
        kpi_bloc_format(
            valeur   = fmt_float(cap_derniere, decimales=1, suffixe=" kWh"),
            label    = "Dernière estimation",
            label2   = delta_texte(delta_cap, decimales=1, suffixe=" kWh"),
            couleur2 = delta_couleur(delta_cap),
        ),
        unsafe_allow_html=True,
    )

with col7:
    cap_7j_moy   = kpi.get("capacite_7j_moy")
    cap_7j_delta = kpi.get("capacite_7j_delta")
    st.markdown(
        kpi_bloc_format(
            valeur   = fmt_float(cap_7j_moy, decimales=1, suffixe=" kWh"),
            label    = "Moyenne 7j",
            label2   = delta_texte(cap_7j_delta, decimales=1, suffixe=" kWh"),
            couleur2 = delta_couleur(cap_7j_delta),
        ),
        unsafe_allow_html=True,
    )

# =============================================================================
# Tableau kilométrage / énergie / consommation / rendement — mois et année
# =============================================================================

st.divider()

entete_tableau_kpi()
ligne_kpi("Mois courant",   kpi.get("km_mois"),   kpi.get("energie_mois"),   kpi.get("conso_kwh_100km_mois"))
ligne_kpi("Année courante", kpi.get("km_annee"),  kpi.get("energie_annee"),  kpi.get("conso_kwh_100km_annee"))

# =============================================================================
# Graphique — énergie ajoutée par jour (30 derniers jours)
# =============================================================================

st.divider()
st.subheader(f"Énergie rechargée par jour — {NB_JOURS} derniers jours")

if serie:
    periodes = [row["periode"]                for row in serie]
    energies = [row.get("energie_totale_kwh") for row in serie]
    kms      = [row.get("km_journee")         for row in serie]
    st.plotly_chart(fig_energie_km(periodes, energies, kms, height=280), width='stretch')
else:
    st.info("Aucune donnée disponible pour le graphique.")
