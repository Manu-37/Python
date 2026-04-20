from sysclasses.tools import Tools
import streamlit as st
from datetime import date, timedelta
from enum import IntEnum

#----------------------------------------------------------------------------
# Helpers de formatage — définis dans Tools, réexportés ici pour les pages
#----------------------------------------------------------------------------
fmt_float  = Tools.fmt_float
km_par_kwh = Tools.km_par_kwh

#----------------------------------------------------------------------------
# Design system — spécifique à ce projet Streamlit
#----------------------------------------------------------------------------
COULEURS = {
    "km"        : "#4f7ff7",
    "energie"   : "#ebba19",
    "conso"     : "#3cc343",
    "rendementk": "#811e9cff",
    "titre"     : "#FFFFFF",
    "delta_zero": "#4fc3f7",
    "capacite"  : "#00bcd4",   # cyan-teal
}

FONT_SIZE = {
    "kpi"      : "2.00rem",
    "kpi_small": "1.00rem",
    "label"    : "1.00rem",
}

#----------------------------------------------------------------------------
# Procédures de formatage de KPI et autres éléments d'interface — utilisées dans les pages
#----------------------------------------------------------------------------
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

def couleur_pale(hex_color: str, opacite: float = 0.35) -> str:
    """
    Éclaircit une couleur hex en la mélangeant avec le fond du thème actif.
    Lit backgroundColor depuis la config Streamlit — s'adapte à tout thème.
    opacite : 1.0 = couleur originale, 0.0 = fond pur
    """
    
    fond_hex = st.get_option("theme.backgroundColor") or "#0e1117"

    fond_r = int(fond_hex[1:3], 16)
    fond_g = int(fond_hex[3:5], 16)
    fond_b = int(fond_hex[5:7], 16)

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    r_pale = round(r * opacite + fond_r * (1 - opacite))
    g_pale = round(g * opacite + fond_g * (1 - opacite))
    b_pale = round(b * opacite + fond_b * (1 - opacite))

    return f"#{r_pale:02x}{g_pale:02x}{b_pale:02x}"

def decaler_date(d: date, duree: str) -> date:
    from dateutil.relativedelta import relativedelta
    match duree:
        case "Semaine"   : return d - timedelta(weeks=1)
        case "Mois"      : return d - relativedelta(months=1)
        case "Trimestre" : return d - relativedelta(months=3)
        case "Semestre"  : return d - relativedelta(months=6)
        case "Année"     : return d - relativedelta(years=1)
        case _           : return d - relativedelta(months=1)

class Serie(IntEnum):
    EN_COURS  = 0
    REFERENCE = 1