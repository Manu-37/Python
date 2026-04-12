from ..clsTstatData_STAT import clsTstatData_STAT


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

    def journee(self, veh_id: int, date_jour: str = None) -> dict | None:
        """
        Données d'un jour donné, ou du dernier jour disponible si date_jour est None.

        Retourne un dict enrichi :
            date_jour                      — date de la journée
            odometer_delta_miles           — distance brute (miles, unité native)
            km_journee                     — calculé : odometer_delta_miles × 1.60934
            nb_snapshots
            energie_ajoutee_kwh            — NULL si pas de charge
            capacite_estimee_kwh           — NULL si pas de charge
            soc_debut_pct / soc_fin_pct    — NULL si pas de charge
            odometer_debut / odometer_fin  — NULL si pas de charge
            miles_depuis_charge_precedente — NULL si pas de charge
            session_num_debut / fin        — NULL si pas de charge
            conso_kwh_100km                — calculé ; None si km = 0 ou énergie absente
        Retourne None si aucune donnée.
        """
        where, params = self._build_where({
            "veh_id"   : veh_id,
            "date_jour": date_jour,
        })

        sql = f"""
            SELECT *
            FROM {self._schema}.{self._table}
            {where}
            ORDER BY date_jour DESC
            LIMIT 1
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if not rows:
            return None

        row   = dict(rows[0])
        miles = row.get("odometer_delta_miles")
        kwh   = row.get("energie_ajoutee_kwh")

        km    = round(float(miles) * 1.60934, 1) if miles is not None else None
        conso = round(float(kwh) / km * 100, 1)  if km and km > 0 and kwh else None

        row["km_journee"]      = km
        row["conso_kwh_100km"] = conso
        return row

    def energie_par_jour(
        self,
        veh_id    : int,
        date_debut: str = None,
    ) -> list[dict]:
        """
        Énergie ajoutée et distance par jour depuis date_debut.
        Couvre tous les jours avec snapshots — les jours sans charge ont
        energie_ajoutee_kwh = NULL.

        Retourne par jour :
            periode              — date_jour (DATE)
            energie_totale_kwh   — énergie ajoutée (kWh), NULL si pas de recharge
            odometer_delta_miles — distance brute (miles, unité native)
        """
        where, params = self._build_where({
            "veh_id"        : veh_id,
            "date_jour__gte": date_debut,
        })

        sql = f"""
            SELECT
                date_jour               AS periode,
                energie_ajoutee_kwh     AS energie_totale_kwh,
                odometer_delta_miles
            FROM {self._schema}.{self._table}
            {where}
            ORDER BY date_jour ASC
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
