"""
ctrl_charge.py — Assemblage des données de la page d'accueil.

Rôle :
    Orchestre les appels aux classes Q et retourne des dicts prêts à l'emploi
    pour la couche cache (cache_charge.py) puis la couche UI (charge.py).
    Aucune logique Streamlit ici — fonctions Python pures.

Sources :
    clsQ_journee           — mv_journee (MV4) : tous les jours avec snapshots
    clsQ_charge_sessions_ext — mv_charge_sessions_ext (MV2) : sessions brutes
"""

from db.db_tstat_data import clsQ_journee, clsQ_charge_sessions_ext
from datetime import date
from utilis import debut_periode, Serie
from sysclasses.tools import Tools

_GRANULARITE = {
    "Semaine"  : "jour",
    "Mois"     : "jour",
    "Trimestre": "semaine",
    "Semestre" : "semaine",
    "Année"    : "mois",
}

def _rang(periode: date, debut: date, granularite: str) -> int:
    """Position 1-based d'une ligne dans la période calendaire.
    Garantit que le jour 1 de chaque période s'aligne sur le même rang,
    indépendamment du premier jour avec données.
    """
    match granularite:
        case "jour"   : return (periode - debut).days + 1
        case "semaine": return (periode - debut).days // 7 + 1
        case "mois"   : return (periode.year - debut.year) * 12 + (periode.month - debut.month) + 1
        case _        : return (periode - debut).days + 1

def serie_sessions(veh_id: int, duree: str, date_fin: date) -> list[dict]:
    """Sessions brutes sur la période, enrichies des colonnes km par _apply_computed."""
    q = clsQ_charge_sessions_ext()
    return q.sessions_recentes(veh_id, str(debut_periode(date_fin, duree)), str(date_fin))

def courbe_session(snp_id_debut: int, snp_id_fin: int) -> list[dict]:
    """Points de charge bruts pour une session (pour le graphique de courbe)."""
    return clsQ_charge_sessions_ext().courbe_session(snp_id_debut, snp_id_fin)

def serie_capacite_glissante(veh_id:int, nb_points:int, duree:str, date_fin:date):
    q = clsQ_journee()
    return q.capacite_glissante(veh_id, debut_periode(date_fin, duree), date_fin, nb_points)

def serie_energie_par_periode(veh_id:int, duree:str, date_fin:date, date_comparaison:date)-> dict[int, list[dict]]:
    q    = clsQ_journee()
    gran = _GRANULARITE[duree]

    debut_en_cours  = debut_periode(date_fin, duree)
    debut_reference = debut_periode(date_comparaison, duree)

    donnees = {
        Serie.EN_COURS : (q.energie_par_jour(veh_id, debut_en_cours,  date_fin,         gran), debut_en_cours),
        Serie.REFERENCE: (q.energie_par_jour(veh_id, debut_reference, date_comparaison, gran), debut_reference),
    }

    serie = {}
    for cle, (rows, debut) in donnees.items():
        total_kwh = 0.0
        total_km  = 0.0
        for row in rows:
            row["rang"] = _rang(row["periode"], debut, gran)
            miles = row.get("odometer_delta_miles")
            kwh   = row.get("energie_totale_kwh")
            km    = Tools.miles_to_km(miles, 1) if miles is not None else None
            row["km_periode"]      = km
            if km and km > 0:
                row["conso_kwh_100km"] = round(float(kwh) / km * 100, 1) if kwh else 0
            else:
                row["conso_kwh_100km"] = None
            if km  is not None: total_km  += km
            if kwh is not None: total_kwh += float(kwh)
        moyenne = round(total_kwh / total_km * 100, 1) if total_km > 0 else None
        for row in rows:
            row["moyenne_conso_kwh_100km"] = moyenne
        serie[cle] = rows

    return serie
