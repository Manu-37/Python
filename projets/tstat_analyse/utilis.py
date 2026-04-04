from sysclasses.tools import Tools

# Helpers de formatage — définis dans Tools, réexportés ici pour les pages
fmt_float = Tools.fmt_float
fmt_date  = Tools.fmt_date

# Design system — spécifique à ce projet Streamlit
COULEURS = {
    "km"     : "#4f7ff7",
    "energie": "#ebba19",
    "conso"  : "#3cc343",
    "titre"  : "#FFFFFF",
}

FONT_SIZE = {
    "kpi"      : "2.00rem",
    "kpi_small": "1.00rem",
    "label"    : "1.00rem",
}


def kpi_bloc_format(
    valeur        : str,
    couleur       : str = COULEURS["titre"],
    label         : str = "",
    couleur_label : str = COULEURS["titre"],
    label2        : str = "",
    couleur2      : str = COULEURS["titre"],
) -> str:
    """
    Génère le HTML d'un bloc KPI à trois zones verticales :

        label   — texte au-dessus, taille kpi_small
        valeur  — valeur principale, taille kpi, en gras
        label2  — annotation en dessous, taille kpi_small

    Chaque zone a sa couleur indépendante.
    Les zones vides (chaîne vide) ne génèrent pas de balise.

    Usage dans une page Streamlit :
        st.markdown(
            kpi_bloc_format("408 km", COULEURS["km"], label="Kilométrage"),
            unsafe_allow_html=True,
        )
    """
    html = ""
    if label:
        html += (
            f"<p style='color:{couleur_label}; font-size:{FONT_SIZE['kpi_small']}; margin:0 0 2px 0'>"
            f"{label}</p>"
        )
    html += (
        f"<p style='color:{couleur}; font-size:{FONT_SIZE['kpi']}; font-weight:600; margin:0'>"
        f"{valeur}</p>"
    )
    if label2:
        html += (
            f"<p style='color:{couleur2}; font-size:{FONT_SIZE['kpi_small']}; margin:2px 0 0 0'>"
            f"{label2}</p>"
        )
    return html
