"""
charge.py — Page d'analyse des données de charge.

Disposition :
    Sélecteur véhicule — titre
    
Orchestrateur pur — pas de logique métier ni de calcul.
Toutes les données viennent de cache_charge.py.
"""

import streamlit as st
from datetime import date, timedelta
from cache_ressources import bootstrap
from cache_charge import get_liste_vehicules, get_capacite_glissante, get_energie_par_periode, get_sessions, get_courbe_session
from utilis import decaler_date, debut_periode, Serie
from widgets import ligne_kpi, entete_tableau_kpi
from sysclasses import Tools
from charts import fig_energie_km, fig_consommation, fig_capacite, fig_courbe_session

_MOIS_FR  = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
_JOURS_FR = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]

_NB_POINTS_DEFAUT = {
    "Mois"     : 14,
    "Trimestre": 30,
    "Semestre" : 45,
    "Année"    : 60,
}

_DUREES_TOUTES = ["Semaine", "Mois", "Trimestre", "Semestre", "Année"]

def _label_hover(d: date, duree: str) -> str:
    match duree:
        case "Semaine":
            return f"{_JOURS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}"
        case "Année":
            return f"{_MOIS_FR[d.month - 1]} {d.year}"
        case _:
            return d.strftime("%d/%m/%Y")

def _tick_labels_dates(duree: str, date_debut: date, date_fin: date):
    """Retourne (tickvals, ticktext) pour l'axe X date de l'onglet capacité."""
    match duree:
        case "Trimestre":
            vals, texts = [], []
            d = date_debut
            while d.weekday() != 0:          # avancer jusqu'au premier lundi
                d += timedelta(days=1)
            while d <= date_fin:
                vals.append(d)
                texts.append(d.strftime("%d/%m"))
                d += timedelta(weeks=1)
            return vals, texts
        case "Semestre":
            vals, texts = [], []
            m = date_debut.replace(day=1)
            while m <= date_fin:
                vals.append(m)
                texts.append(_MOIS_FR[m.month - 1])
                m = (m + timedelta(days=32)).replace(day=1)
            return vals, texts
        case "Année":
            vals, texts = [], []
            m = date_debut.replace(day=1)
            while m <= date_fin:
                vals.append(m)
                texts.append(f"{_MOIS_FR[m.month - 1]}\n{m.year}")
                m = (m + timedelta(days=32)).replace(day=1)
            return vals, texts
        case _:
            return None, None


def _tick_labels(duree: str, debut: date, max_rang: int):
    """Retourne (tickvals, ticktext) pour l'axe x selon la granularité."""
    match duree:
        case "Semaine":
            return list(range(1, 8)), _JOURS_FR
        case "Trimestre" | "Semestre":
            vals  = list(range(1, max_rang + 1))
            texts = [(debut + timedelta(weeks=i)).strftime("%d/%m") for i in range(max_rang)]
            return vals, texts
        case "Année":
            return list(range(1, 13)), _MOIS_FR
        case _:
            return None, None


# =============================================================================
# Procédures de chagement des données — appel des fonctions de ctrl_charge.py
# =============================================================================
def selecteurs_periode(
        key_prefix: str,
        index_duree: int = 1,
        avec_moyenne: bool = True,
        avec_comparaison: bool = False,
        durees: list[str] | None = None,
        ) -> tuple:
    """
    Bloc de sélecteurs réutilisable par onglet.
    key_prefix — préfixe unique par onglet (ex: "cap", "nrj", "ses")
    durees     — liste des durées proposées (None = toutes)
    Retourne : (duree, date_fin, nb_points, date_comparaison) — date_comparaison est None si avec_comparaison=False
    """
    options = durees if durees is not None else _DUREES_TOUTES
    nb_cols = [5, 5]
    if avec_moyenne    : nb_cols.append(6)
    if avec_comparaison: nb_cols.append(5)
    nb_cols.append(66 - sum(nb_cols))  # spacer dynamique
    cols = st.columns(nb_cols)

    with cols[0]:
        duree = st.selectbox(
            "Durée d'analyse",
            options=options,
            index=index_duree,
            key=f"{key_prefix}_duree"
        )
    with cols[1]:
        date_fin = st.date_input(
            "Date de fin",
            value=Tools.date_du_jour(),
            format="DD/MM/YYYY",
            key=f"{key_prefix}_date_fin"
        )
    nb_points = None
    if avec_moyenne:
        # Réinitialisation adaptative de nb_points si la durée change
        cle_nb  = f"{key_prefix}_nb_points"
        cle_pnd = f"{key_prefix}_prev_duree_nb"
        if st.session_state.get(cle_pnd) != duree:
            st.session_state[cle_nb] = _NB_POINTS_DEFAUT.get(duree, 30)
        st.session_state[cle_pnd] = duree
        with cols[2]:
            nb_points = st.number_input(
                "Moyenne glissante (jours)",
                min_value=1, max_value=365, step=1,
                key=cle_nb,
            )
    date_comparaison = None
    if avec_comparaison:
        #----------------------------------------------------------------------------
        # Logique de forçage du recalcul de la date de comparaison 
        # si la durée ou la date de fin changent
        #----------------------------------------------------------------------------
        # définir les clés de session_state pour mémoriser les valeurs précédentes
        # on utilise le key_prefix pour éviter les conflits entre onglets
        #----------------------------------------------------------------------------
        cle_comp = f"{key_prefix}_date_comparaison"
        if cle_comp not in st.session_state:
            st.session_state[cle_comp] = decaler_date(date_fin, duree)  # valeur initiale

        cle_prev_duree   = f"{key_prefix}_prev_duree"
        cle_prev_datefin = f"{key_prefix}_prev_datefin"

        duree_a_change   = st.session_state.get(cle_prev_duree)   != duree
        datefin_a_change = st.session_state.get(cle_prev_datefin) != date_fin

        if duree_a_change or datefin_a_change:
            # Recalcul forcé — écrase la valeur dans session_state
            st.session_state[f"{key_prefix}_date_comparaison"] = decaler_date(date_fin, duree)

        # Mémoriser les valeurs courantes pour la prochaine passe
        st.session_state[cle_prev_duree]   = duree
        st.session_state[cle_prev_datefin] = date_fin

        with cols[3 if avec_moyenne else 2]:
            date_comparaison = st.date_input(
                "Date de comparaison",
                format="DD/MM/YYYY",
                key=f"{key_prefix}_date_comparaison"
            )
    return duree, date_fin, nb_points, date_comparaison

def afficher_recharge():
    st.header("Recharge — énergie ajoutée par jour")
    duree, date_fin, nb_points, date_comparaison = selecteurs_periode("nrj", index_duree=1, avec_moyenne=False, avec_comparaison=True) 

    # 
    energie_par_periode = get_energie_par_periode(veh_id=VEH_ID, duree=duree, date_fin=date_fin, date_comparaison=date_comparaison)  # préchauffage du cache
   
    en_cours   = energie_par_periode[Serie.EN_COURS]
    reference  = energie_par_periode[Serie.REFERENCE]

    rangs_main   = [row["rang"]                              for row in en_cours]
    dates_main   = [_label_hover(row["periode"], duree)      for row in en_cours]
    nrj_main     = [float(row["energie_totale_kwh"] or 0)   for row in en_cours]
    km_main      = [float(row["km_periode"] or 0)           for row in en_cours]
    conso_main   = [row["conso_kwh_100km"]                  for row in en_cours]
    moyenne_main = en_cours[0]["moyenne_conso_kwh_100km"]   if en_cours else None

    rangs_ref    = [row["rang"]                              for row in reference]
    dates_ref    = [_label_hover(row["periode"], duree)      for row in reference]
    nrj_ref      = [float(row["energie_totale_kwh"] or 0)   for row in reference]
    km_ref       = [float(row["km_periode"] or 0)           for row in reference]
    conso_ref    = [row["conso_kwh_100km"]                  for row in reference]
    moyenne_ref  = reference[0]["moyenne_conso_kwh_100km"]  if reference else None

    entete_tableau_kpi()
    ligne_kpi(f"Sélection courante ({duree})", sum(km_main), sum(nrj_main), moyenne_main)

    max_rang = max((rangs_ref or [0])[-1] if rangs_ref else 0, rangs_main[-1] if rangs_main else 0)
    tickvals, ticktext = _tick_labels(duree, debut_periode(date_fin, duree), max_rang)

    st.plotly_chart(
        fig_energie_km(rangs_main, nrj_main, km_main, dates_main, rangs_ref, nrj_ref, km_ref, dates_ref, tickvals=tickvals, ticktext=ticktext),
        width='stretch',
    )

    st.plotly_chart(
        fig_consommation(rangs_main, conso_main, moyenne_main, dates_main, rangs_ref, conso_ref, moyenne_ref, dates_ref, tickvals=tickvals, ticktext=ticktext),
        width='stretch',
    )

def afficher_capacite():
    st.header("Capacité estimée — évolution dans le temps")

    duree, date_fin, nb_points, _ = selecteurs_periode(
        "cap",
        index_duree=0,
        avec_moyenne=True,
        avec_comparaison=False,
        durees=["Mois", "Trimestre", "Semestre", "Année"],
    )
    serie = get_capacite_glissante(veh_id=VEH_ID, nb_points=nb_points, duree=duree, date_fin=date_fin)
    if serie:
        periodes = [row["dat_date"]                 for row in serie]
        energies = [row.get("capacite_estimee_kwh") for row in serie]
        moyenne  = [row.get("moy_glissante")        for row in serie]

        date_debut = debut_periode(date_fin, duree)
        tickvals, ticktext = _tick_labels_dates(duree, date_debut, date_fin)

        st.plotly_chart(
            fig_capacite(periodes, energies, moyenne, tickvals=tickvals, ticktext=ticktext),
            width='stretch',
        )
    else:
        st.info("Aucune donnée disponible pour le graphique.")
   
def afficher_sessions():
    import pandas as pd
    from zoneinfo import ZoneInfo
    _PARIS = ZoneInfo("Europe/Paris")

    def _paris(dt):
        return dt.astimezone(_PARIS) if dt else None

    st.header("Sessions de charge")
    duree, date_fin, _, _ = selecteurs_periode("ses", index_duree=1, avec_moyenne=False, avec_comparaison=False)

    sessions = get_sessions(veh_id=VEH_ID, duree=duree, date_fin=date_fin)
    if not sessions:
        st.info("Aucune session de charge sur cette période.")
        return

    lignes = []
    for s in sessions:
        debut   = _paris(s["debut_session"])
        fin     = _paris(s["fin_session"])
        duree_s = int((fin - debut).total_seconds()) if debut and fin else 0
        h, m    = divmod(duree_s // 60, 60)
        km_prec = s.get("km_depuis_charge_precedente")
        lignes.append({
            "Début"           : debut.strftime("%d/%m %H:%M") if debut else "—",
            "Durée"           : f"{h}h{m:02d}"               if duree_s else "—",
            "kWh"             : s.get("energie_ajoutee_kwh"),
            "SOC"             : f"{s['soc_debut_pct']}% → {s['soc_fin_pct']}%",
            "Pmax (kW)"       : s.get("puissance_max_kw"),
            "Type"            : "DC" if s.get("fastcharger") else "AC",
            "État"            : s.get("etat_final", ""),
            "km depuis préc." : round(km_prec, 0) if km_prec is not None else None,
        })

    sel = st.dataframe(
        pd.DataFrame(lignes),
        width='stretch',
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    idx_selectionnes = sel.selection.rows
    if idx_selectionnes:
        s      = sessions[idx_selectionnes[0]]
        courbe = get_courbe_session(s["snp_id_debut"], s["snp_id_fin"])
        if courbe:
            # Conversion UTC → Paris pour l'axe temporel du graphique
            courbe_paris = [
                {**row, "snp_timestamp": _paris(row["snp_timestamp"])}
                for row in courbe
            ]
            type_str = "Superchargeur DC" if s.get("fastcharger") else "AC"
            debut    = _paris(s["debut_session"])
            st.subheader(f"Courbe — {debut.strftime('%d/%m/%Y %H:%M')} · {type_str}")
            st.plotly_chart(fig_courbe_session(courbe_paris), width='stretch')

# =============================================================================
# Initialisations
# =============================================================================
bootstrap()  # charge les variables d'environnement et initialise la config Streamlit
st.set_page_config(page_title="tstat — Charge", page_icon="🔋", layout="wide")


# =============================================================================
# Titre + sélecteur véhicule
# =============================================================================

vehicules = get_liste_vehicules()
with st.container():

    col_titre, col_combo = st.columns([4, 1])
    with col_titre:
        st.title("⚡ Tesla Stats — Analyse des données de charge")
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

# =============================================================================
# Définition de la boite à onglets
# =============================================================================
with st.container():
    ONG_Recharge, ONG_Capacite, ONG_Sessions = st.tabs([
        "Recharge","Capacité", "Sessions récentes"
    ]) 

    with ONG_Recharge:
        afficher_recharge()
    

    with ONG_Capacite:
        afficher_capacite()

    with ONG_Sessions:
        afficher_sessions()


