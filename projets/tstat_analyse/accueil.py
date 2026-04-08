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
import plotly.graph_objects as go
from cache_ressources import bootstrap
from cache_charge import get_kpi_home, get_energie_par_jour, get_liste_vehicules
from utilis import COULEURS, fmt_float, fmt_date, km_par_kwh, kpi_bloc_format, delta_couleur, delta_texte

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

kpi      = get_kpi_home(veh_id=VEH_ID)
serie    = get_energie_par_jour(veh_id=VEH_ID, nb_jours=NB_JOURS)
derniere = kpi.get("derniere_session") or {}
journee  = kpi.get("journee_actuelle") or {}

# =============================================================================
# État courant — 7 colonnes
# Ordre : Dernière charge | Km jour | Énergie | Conso | Rendement | Cap. moy 7j | Cap. dernière
# =============================================================================

st.divider()
st.subheader("État courant")

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    st.markdown(
        kpi_bloc_format(
            valeur = fmt_date(derniere.get("debut_session")),
            label  = "Dernière charge",
            label2 = f"→ {fmt_date(derniere.get('fin_session'))}",
        ),
        unsafe_allow_html=True,
    )

with col2:
    date_jour  = journee.get("date_jour")
    label_date = date_jour.strftime("%d/%m/%Y") if date_jour else "—"
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(journee.get("km_journee"), decimales=0, suffixe=" km"),
            couleur = COULEURS["km"],
            label   = f"Km — {label_date}",
        ),
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(journee.get("energie_ajoutee_kwh"), decimales=1, suffixe=" kWh"),
            couleur = COULEURS["energie"],
            label   = "Énergie rechargée",
        ),
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(journee.get("conso_kwh_100km"), decimales=1, suffixe=" kWh/100km"),
            couleur = COULEURS["conso"],
            label   = "Consommation",
        ),
        unsafe_allow_html=True,
    )

with col5:
    st.markdown(
        kpi_bloc_format(
            valeur  = fmt_float(km_par_kwh(journee.get("km_journee"), journee.get("energie_ajoutee_kwh")), decimales=1, suffixe=" km/kWh"),
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

_, col_km, col_nrj, col_conso, col_rendement, _, _ = st.columns(7)
with col_km:        st.markdown("**Kilométrage**")
with col_nrj:       st.markdown("**Énergie rechargée**")
with col_conso:     st.markdown("**Consommation**")
with col_rendement: st.markdown("**Rendement kilométrique**")

col_label, col_km, col_nrj, col_conso, col_rendement, _, _ = st.columns(7)
with col_label:     st.markdown("<br>**Mois courant**", unsafe_allow_html=True)
with col_km:        st.markdown(kpi_bloc_format(fmt_float(kpi.get("km_mois"),               decimales=0, suffixe=" km"),         COULEURS["km"]),         unsafe_allow_html=True)
with col_nrj:       st.markdown(kpi_bloc_format(fmt_float(kpi.get("energie_mois"),          decimales=1, suffixe=" kWh"),        COULEURS["energie"]),    unsafe_allow_html=True)
with col_conso:     st.markdown(kpi_bloc_format(fmt_float(kpi.get("conso_kwh_100km_mois"),  decimales=1, suffixe=" kWh/100km"), COULEURS["conso"]),      unsafe_allow_html=True)
with col_rendement: st.markdown(kpi_bloc_format(fmt_float(km_par_kwh(kpi.get("km_mois"),    kpi.get("energie_mois")),            decimales=1, suffixe=" km/kWh"), COULEURS["rendementk"]), unsafe_allow_html=True)

col_label, col_km, col_nrj, col_conso, col_rendement, _, _ = st.columns(7)
with col_label:     st.markdown("<br>**Année courante**", unsafe_allow_html=True)
with col_km:        st.markdown(kpi_bloc_format(fmt_float(kpi.get("km_annee"),               decimales=0, suffixe=" km"),         COULEURS["km"]),         unsafe_allow_html=True)
with col_nrj:       st.markdown(kpi_bloc_format(fmt_float(kpi.get("energie_annee"),          decimales=1, suffixe=" kWh"),        COULEURS["energie"]),    unsafe_allow_html=True)
with col_conso:     st.markdown(kpi_bloc_format(fmt_float(kpi.get("conso_kwh_100km_annee"), decimales=1, suffixe=" kWh/100km"), COULEURS["conso"]),      unsafe_allow_html=True)
with col_rendement: st.markdown(kpi_bloc_format(fmt_float(km_par_kwh(kpi.get("km_annee"),   kpi.get("energie_annee")),           decimales=1, suffixe=" km/kWh"), COULEURS["rendementk"]), unsafe_allow_html=True)

# =============================================================================
# Graphique — énergie ajoutée par jour (30 derniers jours)
# =============================================================================

st.divider()
st.subheader(f"Énergie rechargée par jour — {NB_JOURS} derniers jours")

if serie:
    periodes = [row["periode"]                for row in serie]
    energies = [row.get("energie_totale_kwh") for row in serie]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x             = periodes,
        y             = energies,
        name          = "Énergie (kWh)",
        marker_color  = COULEURS["energie"],
        hovertemplate = "%{x|%d/%m/%Y}<br>%{y:.1f} kWh<extra></extra>",
    ))
    fig.update_layout(
        height        = 280,
        margin        = dict(l=40, r=20, t=10, b=40),
        xaxis_title   = None,
        yaxis_title   = "kWh",
        showlegend    = False,
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée disponible pour le graphique.")
