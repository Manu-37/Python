"""
ctrl_accueil.py — Assemblage des données de la page d'accueil.

Rôle :
    Orchestre les appels aux classes Q et retourne des dicts prêts à l'emploi
    pour la couche cache (cache_charge.py) puis la couche UI (accueil.py).
    Aucune logique Streamlit ici — fonctions Python pures.

Sources :
    clsQ_journee           — mv_journee (MV4) : tous les jours avec snapshots
    clsQ_charge_sessions_ext — mv_charge_sessions_ext (MV2) : sessions brutes
"""

from db.db_tstat_data import clsQ_journee, clsQ_charge_sessions_ext
from datetime import date, timedelta


# =============================================================================
# Helper privé
# =============================================================================

def _conso_safe(val: float | None) -> float | None:
    """
    Traduit la valeur sentinel 9999 (km = 0, données présentes)
    en None pour l'affichage — évite un "9999 kWh/100km" absurde dans l'UI.
    """
    if val is None or val == 9999:
        return None
    return val


# =============================================================================
# KPI page d'accueil
# =============================================================================

def kpi_home(veh_id: int) -> dict:
    """
    Assemble tous les KPI scalaires de la page d'accueil en un seul dict.

    Retourne :
        capacite_7j_moy        — capacité estimée moyenne sur les 7 derniers jours (kWh)
        capacite_7j_delta      — delta vs les 7 jours précédents (kWh), None si insuffisant
        derniere_session       — dict de la dernière session (colonnes MV2 + km calculés), None si vide
        journee_actuelle       — dict du dernier jour (colonnes MV4 + km_journee + conso calculés), None si vide
        km_mois                — km parcourus depuis le 1er du mois courant
        km_annee               — km parcourus depuis le 1er janvier
        energie_mois           — kWh ajoutés depuis le 1er du mois courant
        energie_annee          — kWh ajoutés depuis le 1er janvier
        conso_kwh_100km_mois   — kWh/100 km sur le mois courant (None si km = 0 ou pas de données)
        conso_kwh_100km_annee  — kWh/100 km sur l'année courante (None si km = 0 ou pas de données)
        derniere_capacite      — dernière capacité estimée valide (kWh), None si aucune mesure
    """
    q     = clsQ_journee()
    q_ext = clsQ_charge_sessions_ext()

    cap_moy, cap_delta = q.moyenne_capacite_glissante(veh_id, nb_jours=7)
    derniere_recharge  = q.derniere_recharge(veh_id, date.today() - timedelta(days=1))
    periode_mois       = q.donnees_periode(veh_id, "mois")
    periode_annee      = q.donnees_periode(veh_id, "annee")
    derniere_cap       = q.derniere_capacite(veh_id)

    sessions = q_ext.sessions_recentes(veh_id=veh_id, limite=1)

    return {
        "capacite_7j_moy"       : cap_moy,
        "capacite_7j_delta"     : cap_delta,
        "derniere_session"      : sessions[0] if sessions else None,
        "derniere_recharge"     : derniere_recharge,
        "km_mois"               : periode_mois["km_total"],
        "km_annee"              : periode_annee["km_total"],
        "energie_mois"          : periode_mois["energie_totale_kwh"],
        "energie_annee"         : periode_annee["energie_totale_kwh"],
        "conso_kwh_100km_mois"  : _conso_safe(periode_mois["conso_kwh_100km"]),
        "conso_kwh_100km_annee" : _conso_safe(periode_annee["conso_kwh_100km"]),
        "derniere_capacite"     : derniere_cap,
    }


# =============================================================================
# Série temporelle — graphique énergie par jour
# =============================================================================

def serie_energie_par_jour(veh_id: int, date_debut: str, date_fin: str = None) -> list[dict]:
    """
    Énergie ajoutée et kilométrage par jour entre date_debut et date_fin.

    Retourne par jour :
        periode              — date_jour (DATE)
        energie_totale_kwh   — énergie ajoutée (kWh), None si pas de recharge
        odometer_delta_miles — distance brute (miles, unité native)
        km_journee           — calculé : odometer_delta_miles × 1.60934 (1 décimale)
    """
    q    = clsQ_journee()
    rows = q.energie_par_jour(veh_id, date_debut, date_fin)
    for row in rows:
        miles = row.get("odometer_delta_miles")
        row["km_journee"] = round(float(miles) * 1.60934, 1) if miles is not None else None
    return rows
