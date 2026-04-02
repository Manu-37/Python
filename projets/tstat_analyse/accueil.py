"""
Accueil.py — Page d'accueil du dashboard tstat_analyse.

Disposition :
    Ligne 1 : SOC moyen 7j + données vitales de la dernière session
    Ligne 2 : Kilométrage mois / année
    Ligne 3 : Énergie mois / année
    Ligne 4 : Consommation kWh/100km mois / année + dernière capacité
    ──────────────────────────────────────────────────────────────────
    Graphique énergie par jour — pleine largeur (30 derniers jours)

Ce fichier est un orchestrateur — pas de logique métier.
Toutes les données viennent de cache.py.
sys.path résolu par PYTHONPATH passé par run_tstat_analyse.py.
"""

import streamlit as st
import plotly.graph_objects as go
from cache import get_kpi_home, get_energie_par_jour

# =============================================================================
# Configuration de la page
# =============================================================================

st.set_page_config(
    page_title = "tstat — Accueil",
    page_icon  = "⚡",
    layout     = "wide",
)

# =============================================================================
# Paramètres courants
# =============================================================================

VEH_ID   = None   # None = tous les véhicules
NB_JOURS = 30     # fenêtre du graphique énergie par jour

# =============================================================================
# Chargement des données
# =============================================================================

kpi   = get_kpi_home(veh_id=VEH_ID)
serie = get_energie_par_jour(veh_id=VEH_ID, nb_jours=NB_JOURS)

# =============================================================================
# Helpers d'affichage
# =============================================================================

def fmt_float(valeur, decimales: int = 1, suffixe: str = "") -> str:
    """Formate un float ou retourne '—' si None."""
    if valeur is None:
        return "—"
    return f"{round(float(valeur), decimales)}{suffixe}"

def fmt_date(valeur) -> str:
    """Formate un datetime UTC en heure locale ou retourne '—' si None."""
    if valeur is None:
        return "—"
    try:
        from zoneinfo import ZoneInfo
        # Conversion UTC → heure locale
        # zoneinfo gère automatiquement heure d'été / heure d'hiver
        if valeur.tzinfo is not None:
            valeur = valeur.astimezone(ZoneInfo("Europe/Paris"))
        return valeur.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(valeur)

# =============================================================================
# Titre
# =============================================================================

st.title("⚡ Tesla Stats — Tableau de bord")
st.caption(f"Données mises à jour toutes les 5 minutes · Véhicule : {'tous' if VEH_ID is None else VEH_ID}")
st.divider()

# =============================================================================
# Ligne 1 — SOC + dernière session
# =============================================================================

st.subheader("État courant")

derniere = kpi.get("derniere_session") or {}

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        label = "SOC moyen 7j",
        value = fmt_float(kpi.get("soc_glissant_7j"), decimales=1, suffixe=" %"),
    )

with col2:
    st.metric(
        label = "Dernière charge — début",
        value = fmt_date(derniere.get("debut_session")),
    )

with col3:
    st.metric(
        label = "Dernière charge — fin",
        value = fmt_date(derniere.get("fin_session")),
    )

with col4:
    st.metric(
        label = "Énergie ajoutée",
        value = fmt_float(derniere.get("energie_ajoutee_kwh"), decimales=1, suffixe=" kWh"),
    )

with col5:
    st.metric(
        label = "SOC déb. → fin",
        value = (
            f"{fmt_float(derniere.get('soc_debut_pct'), decimales=0, suffixe='%')}"
            f" → "
            f"{fmt_float(derniere.get('soc_fin_pct'), decimales=0, suffixe='%')}"
        ),
    )

with col6:
    cap_derniere   = kpi.get("derniere_capacite")
    cap_precedente = derniere.get("capacite_estimee_kwh")
    delta_cap = None
    if cap_derniere is not None and cap_precedente is not None:
        try:
            delta_cap = round(float(cap_derniere) - float(cap_precedente), 1)
        except Exception:
            delta_cap = None

    st.metric(
        label      = "Capacité estimée",
        value      = fmt_float(cap_derniere, decimales=1, suffixe=" kWh"),
        delta      = fmt_float(delta_cap, decimales=1, suffixe=" kWh") if delta_cap is not None else None,
        delta_color= "normal",
    )

st.divider()

# =============================================================================
# Ligne 2 — Kilométrage
# =============================================================================

st.subheader("Kilométrage")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label = "Km parcourus — mois courant",
        value = fmt_float(kpi.get("km_mois"), decimales=0, suffixe=" km"),
    )

with col2:
    st.metric(
        label = "Km parcourus — année courante",
        value = fmt_float(kpi.get("km_annee"), decimales=0, suffixe=" km"),
    )

st.divider()

# =============================================================================
# Ligne 3 — Énergie
# =============================================================================

st.subheader("Énergie rechargée")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label = "Énergie rechargée — mois courant",
        value = fmt_float(kpi.get("energie_mois"), decimales=1, suffixe=" kWh"),
    )

with col2:
    st.metric(
        label = "Énergie rechargée — année courante",
        value = fmt_float(kpi.get("energie_annee"), decimales=1, suffixe=" kWh"),
    )

st.divider()

# =============================================================================
# Ligne 4 — Consommation
# =============================================================================

st.subheader("Consommation")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label = "Consommation — mois courant",
        value = fmt_float(kpi.get("conso_kwh_100km_mois"), decimales=1, suffixe=" kWh/100km"),
    )

with col2:
    st.metric(
        label = "Consommation — année courante",
        value = fmt_float(kpi.get("conso_kwh_100km_annee"), decimales=1, suffixe=" kWh/100km"),
    )

st.divider()

# =============================================================================
# Graphique — énergie ajoutée par jour (30 derniers jours)
# =============================================================================

st.subheader(f"Énergie rechargée par jour — {NB_JOURS} derniers jours")

if serie:
    periodes = [row["periode"] for row in serie]
    energies = [row.get("energie_totale_kwh") for row in serie]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x             = periodes,
        y             = energies,
        name          = "Énergie (kWh)",
        marker_color  = "#1f77b4",
        hovertemplate = "%{x|%d/%m/%Y}<br>%{y:.1f} kWh<extra></extra>",
    ))
    fig.update_layout(
        height      = 350,
        margin      = dict(l=40, r=20, t=20, b=40),
        xaxis_title = None,
        yaxis_title = "kWh",
        showlegend  = False,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée disponible pour le graphique.")