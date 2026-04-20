from datetime import date
from ..clsTstatData_STAT import clsTstatData_STAT
from sysclasses.tools import Tools


class clsQ_journee(clsTstatData_STAT):
    """
    Requêtes analytiques sur la vue matérialisée mv_journee (MV4).
    Source : synthèse quotidienne complète, ancrée sur les snapshots.
    Couvre TOUS les jours avec au moins un snapshot — y compris les jours sans charge.

    Lecture seule — aucune écriture en base.

    Colonnes disponibles : date_jour, odometer_delta_miles, nb_snapshots,
    energie_ajoutee_kwh (NULL si pas de charge), capacite_estimee_kwh (NULL si pas de charge),
    soc_debut_pct, soc_fin_pct, odometer_debut, odometer_fin,
    miles_depuis_charge_precedente, session_num_debut, session_num_fin.

    Convention : odometer_delta_miles est en miles (unité native Tesla).
    La conversion en km (× 1.60934) est effectuée dans cette classe
    pour les colonnes calculées exposées aux consommateurs.

    Différence avec mv_charge_journee (MV3) :
        MV3 — une ligne seulement les jours où une charge a eu lieu
        MV4 — une ligne pour chaque jour avec des snapshots, charge ou non
    """

    _schema = "public"
    _table  = "mv_journee"

    # =========================================================================
    # Méthodes publiques
    # =========================================================================

    def derniere_recharge(self, veh_id: int, date_limite: date) -> dict | None:
        """
        Données de la dernière journée avec recharge <= date_limite.

        Retourne un dict enrichi :
            date_jour                        — date de la recharge
            energie_ajoutee_kwh              — énergie ajoutée
            capacite_estimee_kwh             — capacité estimée
            soc_debut_pct / soc_fin_pct      — SOC début/fin de recharge
            miles_depuis_charge_precedente   — distance brute depuis la charge précédente
            km_depuis_charge_precedente      — calculé : miles × 1.60934
            conso_kwh_100km                  — calculé sur km_depuis_charge_precedente
            date_recharge_precedente         — date de la recharge précédente (DATE), None si première recharge
        Retourne None si aucune recharge trouvée.
        """
        sql = """
            WITH derniere AS (
                SELECT *
                FROM public.mv_journee
                WHERE energie_ajoutee_kwh IS NOT NULL
                  AND veh_id = %s
                  AND date_jour <= %s
                ORDER BY date_jour DESC
                LIMIT 1
            ),
            precedente AS (
                SELECT date_jour
                FROM public.mv_journee
                WHERE energie_ajoutee_kwh IS NOT NULL
                  AND veh_id = %s
                  AND date_jour < (SELECT date_jour FROM derniere)
                ORDER BY date_jour DESC
                LIMIT 1
            )
            SELECT d.*, p.date_jour AS date_recharge_precedente
            FROM derniere d
            LEFT JOIN precedente p ON true
        """
        rows = self.ogEngine.execute_select(sql, (veh_id, date_limite, veh_id))
        if not rows:
            return None

        row   = dict(rows[0])
        miles = row.get("miles_depuis_charge_precedente")
        kwh   = row.get("energie_ajoutee_kwh")

        km    = round(float(miles) * 1.60934, 1) if miles is not None else None
        conso = round(float(kwh) / km * 100, 1)  if km and km > 0 and kwh else None

        row["km_depuis_charge_precedente"] = km
        row["conso_kwh_100km"]             = conso
        return row

    def energie_par_jour(
        self,
        veh_id    : int,
        date_debut: str,
        date_fin  : str,
        granularite : str = "jour",
    ) -> list[dict]:
        """
        Énergie ajoutée et distance par période entre date_debut et date_fin.
        Jointure sur t_dates_dat pour le groupage calendaire.

        granularite : 'jour' (défaut) | 'semaine' | 'mois'

        Retourne par période :
            rupture              — valeur de groupage (dat_date, dat_semaine ou dat_mois)
            periode              — première date de la période (DATE)
            energie_totale_kwh   — somme énergie ajoutée (kWh), NULL si pas de recharge
            odometer_delta_miles — somme distances (miles bruts, unité native Tesla)
        """
        # Rupture de granularité : La rupture est calculée sur la base des colonnes de la table t_dates_dat
        rupture_granularite = {
            "jour"      : "dat_date",
            "semaine"   : "dat_semaine",
            "mois"      : "dat_mois",
        }
        colonne_rupture = rupture_granularite[granularite]

        where, params = self._build_where({
            "veh_id"        : veh_id,
            "date_jour__gte": date_debut,
            "date_jour__lte": date_fin,
        })

        sql = f"""
            SELECT
                {colonne_rupture}             AS rupture,
                MIN(dat.dat_date)             AS periode,
                SUM(energie_ajoutee_kwh)      AS energie_totale_kwh,
                SUM(odometer_delta_miles)     AS odometer_delta_miles
            FROM public.mv_journee j
            INNER JOIN public.t_dates_dat dat ON j.date_jour = dat.dat_date
            {where}
            GROUP BY {colonne_rupture}
            ORDER BY {colonne_rupture} ASC
        """
        return self.ogEngine.execute_select(sql, params if params else None)

    def derniere_capacite(self, veh_id: int) -> float | None:
        """
        Dernière capacité batterie estimée valide (première valeur non NULL
        en ordre décroissant de date_jour).
        Retourne None si aucune estimation disponible.
        """
        where, params = self._build_where({"veh_id": veh_id})
        and_veh       = ("AND " + where[len("WHERE "):]) if where else ""

        sql = f"""
            SELECT capacite_estimee_kwh
            FROM {self._schema}.{self._table}
            WHERE capacite_estimee_kwh IS NOT NULL
              {and_veh}
            ORDER BY date_jour DESC
            LIMIT 1
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if rows and rows[0]["capacite_estimee_kwh"] is not None:
            return float(rows[0]["capacite_estimee_kwh"])
        return None

    def capacite_glissante(
        self,
        veh_id    : int,
        date_debut: date,
        date_fin  : date,
        nb_points : int = 30,
        ) -> list[dict]:
        """
        Capacité batterie estimée sur les nb_points derniers jours avec données,
        entre date_debut et date_fin.
        Retourne par jour :
            date_jour            — date de la journée
            capacite_estimee_kwh — capacité estimée ce jour-là (NULL si pas de charge)
            moy_glissante        — moyenne glissante sur nb_points jours (NULL si fenêtre incomplète)
        """
        date_limite = Tools.date_en_str(Tools.add_days_to_date(date_debut, -nb_points))
        date_fin_str = Tools.date_en_str(date_fin)
        date_debut_str = Tools.date_en_str(date_debut)

        SQL = f"""
            WITH serie_dates AS (
                    SELECT dat_date
                    FROM public.t_dates_dat
                    WHERE dat_date BETWEEN '{date_debut_str}' AND '{date_fin_str}'
                ),
                fenetre AS (
                    SELECT
                        veh_id,
                        date_jour,
                        capacite_estimee_kwh,
                        AVG(capacite_estimee_kwh) OVER (
                            PARTITION BY veh_id
                            ORDER BY date_jour
                            ROWS BETWEEN {nb_points-1} PRECEDING AND CURRENT ROW
                        ) AS moy_glissante
                    FROM public.mv_journee
                    WHERE capacite_estimee_kwh IS NOT NULL
                    AND veh_id = {veh_id}
                    AND date_jour >= '{date_limite}'::date
                    AND date_jour <= '{date_fin_str}'::date
                )
                SELECT
                    sd.dat_date,
                    f.capacite_estimee_kwh,
                    f.moy_glissante
                FROM serie_dates sd
                LEFT JOIN fenetre f ON f.date_jour = sd.dat_date
                ORDER BY sd.dat_date
        """
        rows = self.ogEngine.execute_select(SQL)
        return [dict(row) for row in rows] if rows else []
    
    def moyenne_capacite_glissante(
        self,
        veh_id  : int,
        nb_jours: int = 30,
    ) -> tuple[float | None, float | None]:
        """
        Capacité batterie moyenne sur les nb_jours derniers jours,
        avec delta vs la période précédente de même longueur.

        Une seule requête — fenêtre de 2×nb_jours séparée en deux moitiés par CASE.

        Retourne :
            (moy_actuelle, delta)
            moy_actuelle — moyenne kWh des nb_jours derniers jours (None si aucune mesure)
            delta        — moy_actuelle − moy_précédente (None si l'une des deux est None)
        """
        where, params = self._build_where({"veh_id": veh_id})
        and_veh       = ("AND " + where[len("WHERE "):]) if where else ""
        fenetre       = nb_jours * 2

        sql = f"""
            SELECT
                ROUND(AVG(CASE WHEN date_jour >= CURRENT_DATE - {nb_jours}
                               THEN capacite_estimee_kwh END)::NUMERIC, 1)
                    AS cap_actuelle,
                ROUND(AVG(CASE WHEN date_jour >= CURRENT_DATE - {fenetre}
                                AND date_jour <  CURRENT_DATE - {nb_jours}
                               THEN capacite_estimee_kwh END)::NUMERIC, 1)
                    AS cap_precedente
            FROM {self._schema}.{self._table}
            WHERE date_jour >= CURRENT_DATE - {fenetre}
              AND capacite_estimee_kwh IS NOT NULL
              {and_veh}
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if not rows:
            return None, None

        cap_actuelle   = rows[0].get("cap_actuelle")
        cap_precedente = rows[0].get("cap_precedente")

        moy = float(cap_actuelle) if cap_actuelle is not None else None
        if moy is not None and cap_precedente is not None:
            delta = round(moy - float(cap_precedente), 1)
        else:
            delta = None

        return moy, delta

    def donnees_periode(self, veh_id: int, periode: str = "mois") -> dict:
        """
        KPI agrégés depuis le début de la période courante.

        periode : 'mois'  → depuis le 1er du mois courant
                  'annee' → depuis le 1er janvier de l'année courante

        Retourne :
            km_total           — km parcourus (odometer_delta_miles × 1.60934), 0.0 si aucun
            energie_totale_kwh — kWh rechargés, 0.0 si aucune recharge
            conso_kwh_100km    — kWh/100 km calculé en base ;
                                  None si aucune donnée sur la période,
                                  9999 si km = 0 (données présentes mais sans déplacement)
        """
        trunc         = "month" if periode == "mois" else "year"
        where, params = self._build_where({"veh_id": veh_id})
        and_veh       = ("AND " + where[len("WHERE "):]) if where else ""

        sql = f"""
            SELECT
                ROUND(
                    (COALESCE(SUM(odometer_delta_miles), 0) * 1.60934)::NUMERIC, 2
                )                                                   AS km_total,
                ROUND(
                    COALESCE(SUM(energie_ajoutee_kwh), 0)::NUMERIC, 2
                )                                                   AS energie_totale_kwh,
                CASE
                    WHEN SUM(odometer_delta_miles) IS NULL THEN NULL
                    WHEN SUM(odometer_delta_miles) = 0     THEN 9999
                    ELSE ROUND(
                        (COALESCE(SUM(energie_ajoutee_kwh), 0)
                         / (SUM(odometer_delta_miles) * 1.60934) * 100)::NUMERIC,
                        2
                    )
                END                                                 AS conso_kwh_100km
            FROM {self._schema}.{self._table}
            WHERE date_jour >= DATE_TRUNC('{trunc}', CURRENT_DATE)
              {and_veh}
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if not rows:
            return {"km_total": 0.0, "energie_totale_kwh": 0.0, "conso_kwh_100km": None}

        row = rows[0]
        return {
            "km_total"          : float(row["km_total"])            if row["km_total"]            is not None else 0.0,
            "energie_totale_kwh": float(row["energie_totale_kwh"])  if row["energie_totale_kwh"]  is not None else 0.0,
            "conso_kwh_100km"   : float(row["conso_kwh_100km"])     if row["conso_kwh_100km"]     is not None else None,
        }
