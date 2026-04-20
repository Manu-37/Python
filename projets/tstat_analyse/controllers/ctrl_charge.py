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

from db.db_tstat_data import clsQ_journee
from datetime import date
from utilis import decaler_date, Serie
from sysclasses.tools import Tools

_GRANULARITE = {
    "Semaine"  : "jour",
    "Mois"     : "jour",
    "Trimestre": "semaine",
    "Semestre" : "semaine",
    "Année"    : "mois",
}

def serie_capacite_glissante(veh_id:int, nb_points:int, duree:str, date_fin:date):
    
    q = clsQ_journee()
    return q.capacite_glissante(veh_id, decaler_date(date_fin, duree), date_fin, nb_points)

def serie_energie_par_periode(veh_id:int, duree:str, date_fin:date, date_comparaison:date)-> dict[int, list[dict]]:
    q = clsQ_journee()

    serie = {}
    serie[Serie.EN_COURS] = q.energie_par_jour(veh_id, decaler_date(date_fin, duree), date_fin, _GRANULARITE[duree])
    serie[Serie.REFERENCE] = q.energie_par_jour(veh_id, decaler_date(date_comparaison, duree), date_comparaison, _GRANULARITE[duree])

    # Post-traitement par série
    for rows in serie.values():
        total_kwh = 0.0
        total_km  = 0.0
        for row in rows:
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
        # Moyenne pondérée de la série (kwh total / km total)
        moyenne = round(total_kwh / total_km * 100, 1) if total_km > 0 else None
        for row in rows:
            row["moyenne_conso_kwh_100km"] = moyenne

    return serie
