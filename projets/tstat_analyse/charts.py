"""
charts.py — Fonctions de construction de figures Plotly réutilisables.

Chaque fonction retourne un go.Figure prêt à passer à st.plotly_chart().
Aucune logique Streamlit, aucun appel DB.
"""

import plotly.graph_objects as go
from utilis import COULEURS, couleur_pale


def fig_energie_km(
    x_main      : list,
    nrj_main    : list,
    km_main     : list,
    labels_main : list = None,
    x_ref       : list = None,
    nrj_ref     : list = None,
    km_ref      : list = None,
    labels_ref  : list = None,
    tickvals    : list = None,
    ticktext    : list = None,
    height      : int  = 320,
) -> go.Figure:
    """
    Barres énergie + ligne km sur axe secondaire.

    Mode accueil  : x_main = dates, labels_main = None  → hover %{x|%d/%m/%Y}
    Mode comparaison : x_main = rangs entiers, labels_main = dates  → hover Jour %{x} — date
    La série de référence (x_ref) utilise toujours des rangs + labels_ref pour le hover.
    """
    fig = go.Figure()

    # Hover adapté : dates directes (accueil) ou rang + date en customdata (charge)
    if labels_main is None:
        nrj_hover_main = "%{x|%d/%m/%Y}<br>%{y:.1f} kWh<extra></extra>"
        km_hover_main  = "%{x|%d/%m/%Y}<br>%{y:.0f} km<extra></extra>"
    else:
        nrj_hover_main = "%{customdata}<br>%{y:.1f} kWh<extra></extra>"
        km_hover_main  = "%{customdata}<br>%{y:.0f} km<extra></extra>"

    fig.add_trace(go.Bar(
        x             = x_main,
        y             = nrj_main,
        name          = "Énergie (période)",
        marker_color  = COULEURS["energie"],
        customdata    = labels_main,
        hovertemplate = nrj_hover_main,
    ))

    if x_ref is not None:
        fig.add_trace(go.Bar(
            x             = x_ref,
            y             = nrj_ref,
            name          = "Énergie (comparaison)",
            marker_color  = couleur_pale(COULEURS["energie"]),
            customdata    = labels_ref,
            hovertemplate = "%{customdata}<br>%{y:.1f} kWh<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x             = x_main,
        y             = km_main,
        yaxis         = "y2",
        name          = "Km (période)",
        mode          = "lines+markers",
        marker_color  = COULEURS["km"],
        customdata    = labels_main,
        hovertemplate = km_hover_main,
    ))

    if x_ref is not None:
        fig.add_trace(go.Scatter(
            x             = x_ref,
            y             = km_ref,
            yaxis         = "y2",
            name          = "Km (comparaison)",
            mode          = "lines+markers",
            marker_color  = couleur_pale(COULEURS["km"]),
            customdata    = labels_ref,
            hovertemplate = "%{customdata}<br>%{y:.0f} km<extra></extra>",
        ))

    xaxis_cfg = dict(title=None)
    if labels_main is not None:
        xaxis_cfg["range"] = [0.5, max((x_ref or x_main)[-1], x_main[-1]) + 0.5] if x_main else None
        if tickvals is not None:
            xaxis_cfg["tickvals"] = tickvals
            xaxis_cfg["ticktext"] = ticktext
        else:
            xaxis_cfg["dtick"] = 1

    fig.update_layout(
        barmode       = "group",
        height        = height,
        margin        = dict(l=40, r=20, t=10, b=40),
        xaxis         = xaxis_cfg,
        yaxis  = dict(title="kWh", side="left",  rangemode="tozero"),
        yaxis2 = dict(title="km",  side="right", overlaying="y", showgrid=False, rangemode="tozero"),
        showlegend    = True,
        legend = dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
    )
    return fig


def fig_consommation(
    x_main      : list,
    conso_main  : list,
    moyenne_main: float,
    labels_main : list = None,
    x_ref       : list = None,
    conso_ref   : list = None,
    moyenne_ref : float = None,
    labels_ref  : list = None,
    tickvals    : list = None,
    ticktext    : list = None,
    height      : int  = 280,
    margin_r    : int  = 73,
) -> go.Figure:
    """
    Ligne de consommation kWh/100km avec moyenne horizontale en pointillés.
    Même convention que fig_energie_km : x rangs + labels en customdata.
    """
    fig = go.Figure()

    if labels_main is None:
        hover_main = "%{x|%d/%m/%Y}<br>%{y:.1f} kWh/100km<extra></extra>"
    else:
        hover_main = "%{customdata}<br>%{y:.1f} kWh/100km<extra></extra>"

    fig.add_trace(go.Scatter(
        x             = x_main,
        y             = conso_main,
        name          = "Conso (période)",
        mode          = "lines+markers",
        connectgaps   = True,
        marker_color  = COULEURS["conso"],
        customdata    = labels_main,
        hovertemplate = hover_main,
    ))
    if x_ref is not None:
        fig.add_trace(go.Scatter(
            x             = x_ref,
            y             = conso_ref,
            name          = "Conso (comparaison)",
            mode          = "lines+markers",
            connectgaps   = True,
            marker_color  = couleur_pale(COULEURS["conso"]),
            customdata    = labels_ref,
            hovertemplate = "%{customdata}<br>%{y:.1f} kWh/100km<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x             = x_main,
        y             = [moyenne_main] * len(x_main),
        name          = "Moyenne (période)",
        mode          = "lines",
        line          = dict(dash="dash"),
        marker_color  = COULEURS["conso"],
        hovertemplate = "%{y:.1f} kWh/100km<extra></extra>",
    ))
    if moyenne_ref is not None:
        fig.add_trace(go.Scatter(
            x             = x_ref,
            y             = [moyenne_ref] * len(x_ref),
            name          = "Moyenne (comparaison)",
            mode          = "lines",
            line          = dict(dash="dash"),
            marker_color  = couleur_pale(COULEURS["conso"]),
            hovertemplate = "%{y:.1f} kWh/100km<extra></extra>",
        ))

    xaxis_cfg = dict(title=None)
    if labels_main is not None:
        xaxis_cfg["range"] = [0.5, max((x_ref or x_main)[-1], x_main[-1]) + 0.5] if x_main else None
        if tickvals is not None:
            xaxis_cfg["tickvals"] = tickvals
            xaxis_cfg["ticktext"] = ticktext
        else:
            xaxis_cfg["dtick"] = 1

    fig.update_layout(
        height        = height,
        margin        = dict(l=40, r=margin_r, t=10, b=40),
        xaxis         = xaxis_cfg,
        yaxis         = dict(title="kWh/100km", rangemode="tozero"),
        showlegend    = True,
        legend        = dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
    )
    return fig


def fig_courbe_session(courbe: list[dict], height: int = 300) -> go.Figure:
    """
    Courbe de charge d'une session : puissance (kW) + SOC (%) en fonction du temps.
    Utile notamment sur les Superchargeurs pour visualiser le throttling.
    """
    ts    = [row["snp_timestamp"]    for row in courbe]
    power = [row["chg_power"]        for row in courbe]
    soc   = [row["chg_batterylevel"] for row in courbe]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x             = ts,
        y             = power,
        name          = "Puissance (kW)",
        mode          = "lines",
        fill          = "tozeroy",
        marker_color  = COULEURS["energie"],
        hovertemplate = "%{x|%H:%M}<br>%{y} kW<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x             = ts,
        y             = soc,
        yaxis         = "y2",
        name          = "SOC (%)",
        mode          = "lines",
        marker_color  = COULEURS["km"],
        hovertemplate = "%{x|%H:%M}<br>%{y} %<extra></extra>",
    ))
    fig.update_layout(
        height        = height,
        margin        = dict(l=40, r=60, t=10, b=40),
        xaxis         = dict(title=None),
        yaxis         = dict(title="kW",    side="left",  rangemode="tozero"),
        yaxis2        = dict(title="SOC %", side="right", overlaying="y", showgrid=False, range=[0, 100]),
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
