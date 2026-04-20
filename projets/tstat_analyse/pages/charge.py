"""
charge.py — Page d'analyse des données de charge.

Disposition :
    Sélecteur véhicule — titre
    
Orchestrateur pur — pas de logique métier ni de calcul.
Toutes les données viennent de cache_charge.py.
"""

import streamlit as st
from datetime import date
from cache_ressources import bootstrap
from cache_charge import get_liste_vehicules, get_capacite_glissante, get_energie_par_periode
from utilis import decaler_date, Serie
from widgets import ligne_kpi, entete_tableau_kpi
from sysclasses import Tools
from charts import fig_energie_km, fig_consommation, fig_capacite


# =============================================================================
# Procédures de chagement des données — appel des fonctions de ctrl_charge.py
# =============================================================================
def selecteurs_periode(
        key_prefix: str, 
        index_duree: int = 1, 
        avec_moyenne: bool = True,
        avec_comparaison: bool = False,
        ) -> tuple:
    """
    Bloc de sélecteurs réutilisable par onglet.
    key_prefix — préfixe unique par onglet (ex: "cap", "nrj", "ses")
    Retourne : (duree, date_fin, nb_points, date_comparaison) — date_comparaison est None si avec_comparaison=False
    """
    nb_cols = [5, 5]
    if avec_moyenne    : nb_cols.append(6)
    if avec_comparaison: nb_cols.append(5)
    nb_cols.append(66 - sum(nb_cols))  # spacer dynamique
    cols = st.columns(nb_cols)
    
    with cols[0]:
        duree = st.selectbox(
            "Durée d'analyse",
            options=["Semaine", "Mois", "Trimestre", "Semestre", "Année"],
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
        with cols[2]:
            nb_points = st.number_input(
                "Moyenne glissante (jours)",
                min_value=1, max_value=365, value=30, step=1,
                key=f"{key_prefix}_nb_points"
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

    # Alignement par position
    dates_main   = [row["periode"]                          for row in en_cours]
    nrj_main     = [float(row["energie_totale_kwh"] or 0)  for row in en_cours]
    km_main      = [float(row["km_periode"] or 0)          for row in en_cours]
    conso_main   = [row["conso_kwh_100km"]                 for row in en_cours]
    moyenne_main = en_cours[0]["moyenne_conso_kwh_100km"]  if en_cours else None

    nrj_ref      = [float(row["energie_totale_kwh"] or 0)  for row in reference]
    km_ref       = [float(row["km_periode"] or 0)          for row in reference]
    dates_ref    = [row["periode"]                          for row in reference]
    conso_ref    = [row["conso_kwh_100km"]                 for row in reference]
    moyenne_ref  = reference[0]["moyenne_conso_kwh_100km"] if reference else None

    entete_tableau_kpi()
    ligne_kpi(f"Sélection courante ({duree})", sum(km_main), sum(nrj_main), moyenne_main)

    st.plotly_chart(
        fig_energie_km(dates_main, nrj_main, km_main, dates_ref, nrj_ref, km_ref, dates_ref),
        use_container_width=True,
    )

    st.plotly_chart(
        fig_consommation(dates_main, conso_main, moyenne_main, conso_ref, moyenne_ref),
        use_container_width=True,
    )

def afficher_capacite():
    st.header("Capacité estimée — évolution dans le temps")
    
    duree, date_fin, nb_points, date_comparaison = selecteurs_periode("cap", index_duree=1) 
    serie =get_capacite_glissante(veh_id=VEH_ID, nb_points=nb_points, duree=duree, date_fin=date_fin)  # préchauffage du cache
    if serie:
        periodes    = [row["dat_date"]                  for row in serie]
        energies    = [row.get("capacite_estimee_kwh")  for row in serie]
        moyenne     = [row.get("moy_glissante")         for row in serie]

        #
        st.plotly_chart(fig_capacite(periodes, energies, moyenne), use_container_width=True)
    else:
        st.info("Aucune donnée disponible pour le graphique.")
   
def afficher_sessions():
    st.header("Sessions de charge récentes")

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


