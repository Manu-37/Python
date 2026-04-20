"""
charts.py — Fonctions de construction de figures Plotly réutilisables.

Chaque fonction retourne un go.Figure prêt à passer à st.plotly_chart().
Aucune logique Streamlit, aucun appel DB.
"""

import plotly.graph_objects as go
from utilis import COULEURS, couleur_pale


def fig_energie_km(
    dates_main       : list,
    nrj_main         : list,
    km_main          : list,
    dates_ref        : list = None,
    nrj_ref          : list = None,
    km_ref           : list = None,
    dates_ref_labels : list = None,
    height           : int  = 320,
) -> go.Figure:
    """
    Barres énergie + ligne km sur axe secondaire.
    Avec ou sans série de comparaison selon les paramètres optionnels.

    dates_ref_labels — dates de la période de référence, affichées dans le hover
                       de la série de comparaison (customdata).
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x            = dates_main,
        y            = nrj_main,
        name         = "Énergie (période)",
        marker_color = COULEURS["energie"],
        hovertemplate= "%{x|%d/%m/%Y}<br>%{y:.1f} kWh<extra></extra>",
    ))

    if dates_ref is not None:
        fig.add_trace(go.Bar(
            x            = dates_main,
            y            = nrj_ref,
            name         = "Énergie (comparaison)",
            marker_color = couleur_pale(COULEURS["energie"]),
            customdata   = dates_ref_labels,
            hovertemplate= "%{x|%d/%m/%Y} ← %{customdata|%d/%m/%Y}<br>%{y:.1f} kWh<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x            = dates_main,
        y            = km_main,
        yaxis        = "y2",
        name         = "Km (période)",
        mode         = "lines+markers",
        marker_color = COULEURS["km"],
        hovertemplate= "%{x|%d/%m/%Y}<br>%{y:.0f} km<extra></extra>",
    ))

    if dates_ref is not None:
        fig.add_trace(go.Scatter(
            x            = dates_main,
            y            = km_ref,
            yaxis        = "y2",
            name         = "Km (comparaison)",
            mode         = "lines+markers",
            marker_color = couleur_pale(COULEURS["km"]),
            customdata   = dates_ref_labels,
            hovertemplate= "%{x|%d/%m/%Y} ← %{customdata|%d/%m/%Y}<br>%{y:.0f} km<extra></extra>",
        ))

    fig.update_layout(
        barmode       = "group",
        height        = height,
        margin        = dict(l=40, r=20, t=10, b=40),
        xaxis_title   = None,
        yaxis  = dict(title="kWh", side="left",  rangemode="tozero"),
        yaxis2 = dict(title="km",  side="right", overlaying="y", showgrid=False, rangemode="tozero"),
        showlegend    = True,
        legend = dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
    )
    return fig


def fig_consommation(
    dates_main   : list,
    conso_main   : list,
    moyenne_main : float,
    conso_ref    : list = None,
    moyenne_ref  : float = None,
    height       : int  = 280,
    margin_r     : int  = 73,
) -> go.Figure:
    """
    Ligne de consommation kWh/100km avec moyenne horizontale en pointillés.
    Avec ou sans série de comparaison selon les paramètres optionnels.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x            = dates_main,
        y            = conso_main,
        name         = "Conso (période)",
        mode         = "lines+markers",
        connectgaps  = True,
        marker_color = COULEURS["conso"],
        hovertemplate= "%{x|%d/%m/%Y}<br>%{y:.1f} kWh/100km<extra></extra>",
    ))
    if conso_ref is not None:
        fig.add_trace(go.Scatter(
            x            = dates_main,
            y            = conso_ref,
            name         = "Conso (comparaison)",
            mode         = "lines+markers",
            connectgaps  = True,
            marker_color = couleur_pale(COULEURS["conso"]),
            hovertemplate= "%{x|%d/%m/%Y}<br>%{y:.1f} kWh/100km<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x            = dates_main,
        y            = [moyenne_main] * len(dates_main),
        name         = "Moyenne (période)",
        mode         = "lines",
        line         = dict(dash="dash"),
        marker_color = COULEURS["conso"],
        hovertemplate= "%{x|%d/%m/%Y}<br>%{y:.1f} kWh/100km<extra></extra>",
    ))
    if moyenne_ref is not None:
        fig.add_trace(go.Scatter(
            x            = dates_main,
            y            = [moyenne_ref] * len(dates_main),
            name         = "Moyenne (comparaison)",
            mode         = "lines",
            line         = dict(dash="dash"),
            marker_color = couleur_pale(COULEURS["conso"]),
            hovertemplate= "%{x|%d/%m/%Y}<br>%{y:.1f} kWh/100km<extra></extra>",
        ))

    fig.update_layout(
        height        = height,
        margin        = dict(l=40, r=margin_r, t=10, b=40),
        xaxis_title   = None,
        yaxis         = dict(title="kWh/100km", rangemode="tozero"),
        showlegend    = True,
        legend        = dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
    )
    return fig


def fig_capacite(
    periodes : list,
    energies : list,
    moyenne  : list,
    height   : int = 280,
) -> go.Figure:
    """
    Courbe de capacité batterie estimée avec moyenne glissante.
    Y-range calculé automatiquement avec marge de 15%.
    """
    y_range = None
    valeurs = [float(v) for v in moyenne + energies if v is not None]
    if valeurs:
        y_min  = min(valeurs)
        y_max  = max(valeurs)
        marge  = (y_max - y_min) * 0.15 or 2
        y_range = [y_min - marge, y_max + marge]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x             = periodes,
        y             = moyenne,
        name          = "Capacité estimée moyenne (kWh)",
        marker_color  = COULEURS["capacite"],
        connectgaps   = True,
        hovertemplate = "%{x|%d/%m/%Y}<br>%{y:.1f} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x             = periodes,
        y             = energies,
        name          = "Capacité estimée jour (kWh)",
        mode          = "lines+markers",
        marker_color  = couleur_pale(COULEURS["capacite"], 0.5),
        connectgaps   = True,
        hovertemplate = "%{x|%d/%m/%Y}<br>%{y:.0f} kWh<extra></extra>",
    ))
    fig.update_layout(
        height        = height,
        margin        = dict(l=40, r=20, t=10, b=40),
        xaxis_title   = None,
        yaxis         = dict(title="kWh", side="left", range=y_range),
        showlegend    = True,
        legend        = dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
    )
    return fig
