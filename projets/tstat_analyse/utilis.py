from sysclasses.tools import Tools

# Helpers de formatage — définis dans Tools, réexportés ici pour les pages
fmt_float  = Tools.fmt_float
fmt_date   = Tools.fmt_date
km_par_kwh = Tools.km_par_kwh

# Design system — spécifique à ce projet Streamlit
COULEURS = {
    "km"        : "#4f7ff7",
    "energie"   : "#ebba19",
    "conso"     : "#3cc343",
    "rendementk": "#811e9cff",
    "titre"     : "#FFFFFF",
    "delta_zero": "#4fc3f7",
}

FONT_SIZE = {
    "kpi"      : "2.00rem",
    "kpi_small": "1.00rem",
    "label"    : "1.00rem",
}


def delta_couleur(val: float) -> str:
    """Vert si positif, rouge si négatif, bleu si nul, blanc si None."""
    if val is None:
        return COULEURS["titre"]
    if val > 0:
        return "#28a745"
    if val < 0:
        return "#dc3545"
    return COULEURS["delta_zero"]


def delta_texte(val: float, decimales: int = 1, suffixe: str = "") -> str:
    """
    Formate un delta avec flèche directionnelle :
        val > 0  → ↑ valeur
        val < 0  → ↓ valeur absolue
        val == 0 → → 0
        val is None → chaîne vide
    """
    if val is None:
        return ""
    if val > 0:
        return f"↑ {fmt_float(val, decimales, suffixe)}"
    if val < 0:
        return f"↓ {fmt_float(abs(val), decimales, suffixe)}"
    return f"→ {fmt_float(0, decimales, suffixe)}"


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
