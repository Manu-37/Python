from sysclasses.tools import Tools
from clsTstatBase import clsTstatBase


class clsTstatCharge(clsTstatBase):
    """
    Analyses statistiques des sessions de charge Tesla.
    Source : mv_charge_sessions_ext (faits bruts — odométre en miles).

    Architecture :
    ┌─────────────────────────────────────────────────────────────────┐
    │  Méthodes publiques                                             │
    │  stats_par_mois(veh_id, date_debut, ...)                        │
    │      → normalisent les paramètres en dict filtres               │
    │      → délèguent à _stats_par_periode()                         │
    ├─────────────────────────────────────────────────────────────────┤
    │  _stats_par_periode(granularite, filtres, agregats)             │
    │      → construit le SQL (SELECT / FROM / WHERE / GROUP BY)      │
    │      → exécute via self.ogEngine.execute_select()               │
    │      → applique _apply_computed() sur le résultat               │
    │      → retourne list[dict]                                      │
    ├─────────────────────────────────────────────────────────────────┤
    │  _build_where(filtres)    hérité clsStatBase                    │
    │  _date_trunc(g, col)      hérité clsStatBase                    │
    │  _apply_computed(rows)    conversions post-agrégation           │
    └─────────────────────────────────────────────────────────────────┘

    Principe de conversion miles → km :
        Les colonnes brutes miles ne sont JAMAIS converties avant ou pendant
        l'agrégation SQL. _apply_computed() ajoute les colonnes _km sur le
        résultat final, sans modifier les brutes. Zéro dérive par arrondi.

    _COLONNES_CALCULEES :
        Format : { nom_col_calculee : (fonction, nom_col_source) }
        _apply_computed() ignore silencieusement les colonnes source absentes
        du résultat (toutes les méthodes n'agrègent pas odometer_*).
    """

    _SCHEMA      = "public"
    _MV          = "mv_charge_sessions_ext"
    _MV_JOURNEE  = "mv_charge_journee"

    _COLONNES_CALCULEES: dict[str, tuple] = {
        "odometer_debut_km"           : (Tools.miles_to_km, "odometer_debut"),
        "odometer_fin_km"             : (Tools.miles_to_km, "odometer_fin"),
        "km_depuis_charge_precedente" : (Tools.miles_to_km, "miles_depuis_charge_precedente"),
    }

    # =========================================================================
    # Métadonnées UI — rustine en attendant la refonte clsResultMetadata
    #
    # Un dict par méthode publique — décrit TOUTES les colonnes du résultat
    # (BDD, agrégats, calculées Python) avec label, width, anchor.
    # Consommé directement par la couche Streamlit.
    # Format : { nom_colonne : {"label": str, "width": int, "anchor": "w"|"e"} }
    # =========================================================================

    UI_SESSIONS_PERIODE: dict = {
        "periode"              : {"label": "Période",              "width": 130, "anchor": "w"},
        "nb_sessions"          : {"label": "Sessions",             "width":  80, "anchor": "e"},
        "energie_totale_kwh"   : {"label": "Énergie tot. (kWh)",   "width": 130, "anchor": "e"},
        "energie_moyenne_kwh"  : {"label": "Énergie moy. (kWh)",   "width": 130, "anchor": "e"},
        "soc_debut_moyen_pct"  : {"label": "SOC déb. moy. %",      "width": 110, "anchor": "e"},
        "soc_fin_moyen_pct"    : {"label": "SOC fin moy. %",       "width": 110, "anchor": "e"},
    }

    UI_CAPACITE_PERIODE: dict = {
        "periode"              : {"label": "Période",              "width": 130, "anchor": "w"},
        "nb_mesures"           : {"label": "Mesures",              "width":  80, "anchor": "e"},
        "capacite_moyenne_kwh" : {"label": "Capacité moy. (kWh)",  "width": 140, "anchor": "e"},
        "capacite_min_kwh"     : {"label": "Capacité min (kWh)",   "width": 140, "anchor": "e"},
        "capacite_max_kwh"     : {"label": "Capacité max (kWh)",   "width": 140, "anchor": "e"},
    }

    UI_KILOMETRAGE_PERIODE: dict = {
        "periode"                       : {"label": "Période",                  "width": 130, "anchor": "w"},
        "nb_sessions"                   : {"label": "Sessions",                 "width":  80, "anchor": "e"},
        "km_total_depuis_charge_prec"   : {"label": "Distance tot. (km)",       "width": 130, "anchor": "e"},
        "km_moyen_depuis_charge_prec"   : {"label": "Distance moy. (km)",       "width": 130, "anchor": "e"},
        "miles_total_depuis_charge_prec": {"label": "Distance tot. (mi)",       "width": 130, "anchor": "e"},
        "miles_moyen_depuis_charge_prec": {"label": "Distance moy. (mi)",       "width": 130, "anchor": "e"},
    }

    UI_SESSIONS_RECENTES: dict = {
        "veh_id"                       : {"label": "Véhicule",              "width":  80, "anchor": "e"},
        "session_num"                  : {"label": "N° session",            "width":  80, "anchor": "e"},
        "debut_session"                : {"label": "Début",                 "width": 150, "anchor": "w"},
        "fin_session"                  : {"label": "Fin",                   "width": 150, "anchor": "w"},
        "soc_debut_pct"                : {"label": "SOC déb. %",            "width":  90, "anchor": "e"},
        "soc_fin_pct"                  : {"label": "SOC fin %",             "width":  90, "anchor": "e"},
        "energie_ajoutee_kwh"          : {"label": "Énergie (kWh)",         "width": 110, "anchor": "e"},
        "capacite_estimee_kwh"         : {"label": "Capacité est. (kWh)",   "width": 140, "anchor": "e"},
        "etat_final"                   : {"label": "État",                  "width": 100, "anchor": "w"},
        "odometer_debut"               : {"label": "Odomètre déb. (mi)",    "width": 130, "anchor": "e"},
        "odometer_fin"                 : {"label": "Odomètre fin (mi)",     "width": 130, "anchor": "e"},
        "odometer_debut_km"            : {"label": "Odomètre déb. (km)",    "width": 130, "anchor": "e"},
        "odometer_fin_km"              : {"label": "Odomètre fin (km)",     "width": 130, "anchor": "e"},
        "miles_depuis_charge_precedente": {"label": "Depuis préc. (mi)",    "width": 120, "anchor": "e"},
        "km_depuis_charge_precedente"  : {"label": "Depuis préc. (km)",     "width": 120, "anchor": "e"},
    }

    # =========================================================================
    # Méthodes publiques — interface lisible pour la couche UI
    # =========================================================================

    def sessions_par_periode(
        self,
        granularite : str  = "mois",
        veh_id      : int  = None,
        date_debut  : str  = None,
        date_fin    : str  = None,
        etat_final  : str  = None,
    ) -> list[dict]:
        """
        Nombre de sessions et énergie totale ajoutée par période.

        Retourne par période :
            periode                  — début de période (DATE_TRUNC)
            nb_sessions              — nombre de sessions
            energie_totale_kwh       — somme énergie ajoutée (kWh)
            energie_moyenne_kwh      — moyenne énergie par session (kWh)
            soc_debut_moyen_pct      — SOC moyen en début de session
            soc_fin_moyen_pct        — SOC moyen en fin de session
        """
        filtres  = self._build_filtres(veh_id, date_debut, date_fin, etat_final)
        agregats = {
            "nb_sessions"         : "COUNT(*)",
            "energie_totale_kwh"  : "ROUND(SUM(energie_ajoutee_kwh)::NUMERIC, 2)",
            "energie_moyenne_kwh" : "ROUND(AVG(energie_ajoutee_kwh)::NUMERIC, 2)",
            "soc_debut_moyen_pct" : "ROUND(AVG(soc_debut_pct)::NUMERIC, 1)",
            "soc_fin_moyen_pct"   : "ROUND(AVG(soc_fin_pct)::NUMERIC, 1)",
        }
        return self._stats_par_periode(granularite, filtres, agregats, "debut_session")

    def capacite_par_periode(
        self,
        granularite : str  = "mois",
        veh_id      : int  = None,
        date_debut  : str  = None,
        date_fin    : str  = None,
    ) -> list[dict]:
        """
        Évolution de la capacité batterie estimée par période.
        Seules les sessions avec capacite_estimee_kwh non NULL sont incluses.

        Retourne par période :
            periode                   — début de période (DATE_TRUNC)
            nb_mesures                — nombre de sessions avec capacité estimée
            capacite_moyenne_kwh      — moyenne capacité estimée
            capacite_min_kwh          — minimum (meilleure estimation basse)
            capacite_max_kwh          — maximum (meilleure estimation haute)
        """
        filtres = self._build_filtres(veh_id, date_debut, date_fin)
        # Filtre additionnel : on exclut les sessions sans capacité estimée
        filtres["capacite_estimee_kwh__notnull"] = None
        agregats = {
            "nb_mesures"          : "COUNT(*)",
            "capacite_moyenne_kwh": "ROUND(AVG(capacite_estimee_kwh)::NUMERIC, 1)",
            "capacite_min_kwh"    : "ROUND(MIN(capacite_estimee_kwh)::NUMERIC, 1)",
            "capacite_max_kwh"    : "ROUND(MAX(capacite_estimee_kwh)::NUMERIC, 1)",
        }
        return self._stats_par_periode(granularite, filtres, agregats, "debut_session")

    def kilometrage_par_periode(
        self,
        granularite : str  = "mois",
        veh_id      : int  = None,
        date_debut  : str  = None,
        date_fin    : str  = None,
    ) -> list[dict]:
        """
        Kilométrage parcouru entre charges par période.
        Basé sur miles_depuis_charge_precedente (brut Tesla) converti en km.
        Les sessions sans valeur (1ère session du véhicule) sont exclues.

        Retourne par période :
            periode                        — début de période (DATE_TRUNC)
            nb_sessions                    — nombre de sessions avec distance connue
            km_total_depuis_charge_prec    — somme distances inter-charges (km)
            km_moyen_depuis_charge_prec    — distance moyenne inter-charges (km)
            miles_total_depuis_charge_prec — idem en miles bruts (conservé pour audit)
            miles_moyen_depuis_charge_prec — idem en miles bruts
        """
        filtres = self._build_filtres(veh_id, date_debut, date_fin)
        filtres["miles_depuis_charge_precedente__notnull"] = None
        agregats = {
            "nb_sessions"                    : "COUNT(*)",
            "miles_total_depuis_charge_prec" : "ROUND(SUM(miles_depuis_charge_precedente)::NUMERIC, 3)",
            "miles_moyen_depuis_charge_prec" : "ROUND(AVG(miles_depuis_charge_precedente)::NUMERIC, 3)",
        }
        rows = self._stats_par_periode(granularite, filtres, agregats, "debut_session")

        # Colonnes calculées spécifiques à cette méthode
        # (miles_depuis_charge_precedente n'est pas dans _COLONNES_CALCULEES standard
        #  car ici on travaille sur les agrégats, pas sur la colonne brute)
        for row in rows:
            if row.get("miles_total_depuis_charge_prec") is not None:
                row["km_total_depuis_charge_prec"] = Tools.miles_to_km(
                    row["miles_total_depuis_charge_prec"], decimales=2
                )
            if row.get("miles_moyen_depuis_charge_prec") is not None:
                row["km_moyen_depuis_charge_prec"] = Tools.miles_to_km(
                    row["miles_moyen_depuis_charge_prec"], decimales=2
                )
        return rows

    def sessions_recentes(
        self,
        veh_id  : int = None,
        limite  : int = 50,
    ) -> list[dict]:
        """
        Dernières sessions brutes sans agrégation périodique.
        Utile pour un tableau de détail ou un débogage rapide.

        Retourne les colonnes brutes de mv_charge_sessions_ext
        + colonnes calculées km ajoutées par _apply_computed().

        Paramètres :
            veh_id : filtre véhicule (None = tous)
            limite : nombre max de lignes retournées (défaut 50)
        """
        filtres       = self._build_filtres(veh_id)
        where, params = self._build_where(filtres)

        sql = f"""
            SELECT
                veh_id,
                session_num,
                debut_session,
                fin_session,
                soc_debut_pct,
                soc_fin_pct,
                energie_ajoutee_kwh,
                capacite_estimee_kwh,
                etat_final,
                odometer_debut,
                odometer_fin,
                miles_depuis_charge_precedente
            FROM {self._SCHEMA}.{self._MV}
            {where}
            ORDER BY debut_session DESC
            LIMIT {int(limite)}
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        return self._apply_computed(rows)

    # =========================================================================
    # Méthodes publiques — KPI page d'accueil
    #
    # Principe : un KPI = une méthode = une requête.
    # kpi_home() est un assembleur qui appelle les méthodes unitaires.
    # Chaque méthode unitaire est indépendante et réutilisable seule.
    # =========================================================================

    def kpi_home(self, veh_id: int = None) -> dict:
        """
        Assemble tous les KPI de la page d'accueil en un seul dict.
        Chaque valeur provient d'une méthode indépendante (une requête chacune).

        Retourne :
            capacite_7j_moy        — capacité estimée moyenne sur les 7 derniers jours (kWh)
            capacite_7j_delta      — delta vs les 7 jours précédents (kWh), None si insuffisant
            derniere_session       — dict de la dernière session (ou None)
            km_mois                — km parcourus depuis le 1er du mois courant
            km_annee               — km parcourus depuis le 1er janvier
            energie_mois           — kWh ajoutés depuis le 1er du mois courant
            energie_annee          — kWh ajoutés depuis le 1er janvier
            conso_kwh_100km_mois   — consommation kWh/100km sur le mois courant
            conso_kwh_100km_annee  — consommation kWh/100km sur l'année courante
            derniere_capacite      — dernière capacité estimée valide (kWh) ou None
        """
        cap_7j, cap_7j_delta = self._capacite_glissante_7j(veh_id)
        return {
            "capacite_7j_moy"       : cap_7j,
            "capacite_7j_delta"     : cap_7j_delta,
            "derniere_session"      : self._derniere_session(veh_id),
            "journee_actuelle"      : self._journee_actuelle(veh_id),
            "km_mois"               : self._km_periode(veh_id, "mois"),
            "km_annee"              : self._km_periode(veh_id, "annee"),
            "energie_mois"          : self._energie_periode(veh_id, "mois"),
            "energie_annee"         : self._energie_periode(veh_id, "annee"),
            "conso_kwh_100km_mois"  : self._conso_periode(veh_id, "mois"),
            "conso_kwh_100km_annee" : self._conso_periode(veh_id, "annee"),
            "derniere_capacite"     : self._derniere_capacite(veh_id),
        }

    # =========================================================================
    # Méthode générique privée — cœur de construction et d'exécution
    # =========================================================================

    def _stats_par_periode(
        self,
        granularite    : str,
        filtres        : dict,
        agregats       : dict,
        colonne_date   : str = "debut_session",
    ) -> list[dict]:
        """
        Construit et exécute une requête d'agrégation périodique.

        Paramètres :
            granularite  : clé française — 'jour', 'semaine', 'mois',
                           'trimestre', 'semestre', 'annee'
            filtres      : dict de filtres au format _build_where()
            agregats     : dict { alias_colonne : expression_sql_agregat }
                           ex: {"nb_sessions": "COUNT(*)",
                                "energie_totale_kwh": "SUM(energie_ajoutee_kwh)"}
            colonne_date : colonne temporelle sur laquelle appliquer DATE_TRUNC

        Retourne :
            list[dict] — une ligne par période, triée par période ASC,
                         avec colonnes calculées _km ajoutées par _apply_computed().

        Le SQL généré suit toujours la forme :
            SELECT
                <date_trunc_expr> AS periode,
                <agregat_1>       AS <alias_1>,
                ...
            FROM <schema>.<mv>
            <WHERE ...>
            GROUP BY 1
            ORDER BY 1
        """
        date_trunc_expr = self._date_trunc(granularite, colonne_date)
        where, params   = self._build_where(filtres)

        select_agregats = ",\n                ".join(
            f"{expr} AS {alias}"
            for alias, expr in agregats.items()
        )

        sql = f"""
            SELECT
                {date_trunc_expr} AS periode,
                {select_agregats}
            FROM {self._SCHEMA}.{self._MV}
            {where}
            GROUP BY 1
            ORDER BY 1
        """

        self.ogLog.debug(
            f"clsTstatCharge._stats_par_periode | {granularite} | "
            f"filtres={filtres} | agregats={list(agregats.keys())}"
        )

        rows = self.ogEngine.execute_select(sql, params if params else None)
        return self._apply_computed(rows)

    # =========================================================================
    # Helpers privés — KPI unitaires
    # =========================================================================

    def _journee_actuelle(self, veh_id: int = None) -> dict | None:
        """
        Dernière journée avec au moins une charge dans mv_charge_journee.
        Retourne un dict enrichi avec km_journee et conso_kwh_100km calculés.
        Retourne None si aucune donnée.
        """
        ph        = self.ogEngine.placeholder
        params    = []
        where_veh = ""
        if veh_id is not None:
            where_veh = f"WHERE veh_id = {ph}"
            params.append(veh_id)

        sql = f"""
            SELECT
                date_jour,
                energie_ajoutee_kwh,
                miles_depuis_charge_precedente,
                capacite_estimee_kwh
            FROM public.mv_charge_journee
            {where_veh}
            ORDER BY date_jour DESC
            LIMIT 1
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if not rows:
            return None

        row   = dict(rows[0])
        miles = row.get("miles_depuis_charge_precedente")
        kwh   = row.get("energie_ajoutee_kwh")

        km    = round(float(miles) * 1.60934, 1) if miles is not None else None
        conso = round(float(kwh) / km * 100, 1) if km and km > 0 and kwh else None

        row["km_journee"]      = km
        row["conso_kwh_100km"] = conso
        return row

    def _capacite_glissante_7j(
        self, veh_id: int = None
    ) -> tuple[float | None, float | None]:
        """
        Capacité batterie estimée moyennée sur les 7 derniers jours,
        avec delta vs les 7 jours précédents.

        Une seule requête sur mv_charge_journee — fenêtre de 14 jours,
        séparée en deux moitiés par CASE.

        Retourne :
            (moy_actuelle, delta)
            - moy_actuelle : moyenne kWh des 7 derniers jours (None si aucune mesure)
            - delta        : moy_actuelle − moy_precedente (None si l'une des deux est None)
        """
        ph        = self.ogEngine.placeholder
        params    = []
        where_veh = ""
        if veh_id is not None:
            where_veh = f"AND veh_id = {ph}"
            params.append(veh_id)

        sql = f"""
            SELECT
                ROUND(AVG(CASE WHEN date_jour >= CURRENT_DATE - 7
                               THEN capacite_estimee_kwh END)::NUMERIC, 1)
                    AS cap_actuelle,
                ROUND(AVG(CASE WHEN date_jour >= CURRENT_DATE - 14
                                AND date_jour <  CURRENT_DATE - 7
                               THEN capacite_estimee_kwh END)::NUMERIC, 1)
                    AS cap_precedente
            FROM {self._SCHEMA}.{self._MV_JOURNEE}
            WHERE date_jour >= CURRENT_DATE - 14
              AND capacite_estimee_kwh IS NOT NULL
              {where_veh}
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if not rows:
            return None, None

        cap_actuelle  = rows[0].get("cap_actuelle")
        cap_precedente = rows[0].get("cap_precedente")

        moy = float(cap_actuelle) if cap_actuelle is not None else None
        if moy is not None and cap_precedente is not None:
            delta = round(moy - float(cap_precedente), 1)
        else:
            delta = None

        return moy, delta

    def _derniere_session(self, veh_id: int = None) -> dict | None:
        """
        Retourne la dernière session connue (toutes colonnes + calculées km).
        Retourne None si aucune session en base.
        """
        rows = self.sessions_recentes(veh_id=veh_id, limite=1)
        return rows[0] if rows else None

    def _km_periode(self, veh_id: int = None, periode: str = "mois") -> float | None:
        """
        Km parcourus depuis le début de la période courante.
        Basé sur la somme de miles_depuis_charge_precedente de mv_charge_journee.

        periode : 'mois'  → depuis le 1er du mois courant
                  'annee' → depuis le 1er janvier de l'année courante

        Les jours sans valeur (première session du véhicule) sont exclus.
        Retourne None si aucune donnée sur la période.
        """
        trunc     = "month" if periode == "mois" else "year"
        ph        = self.ogEngine.placeholder
        params    = []
        where_veh = ""
        if veh_id is not None:
            where_veh = f"AND veh_id = {ph}"
            params.append(veh_id)

        sql = f"""
            SELECT ROUND(
                SUM(miles_depuis_charge_precedente) * 1.60934
                ::NUMERIC, 2
            ) AS km_total
            FROM {self._SCHEMA}.{self._MV_JOURNEE}
            WHERE date_jour >= DATE_TRUNC('{trunc}', CURRENT_DATE)
              AND miles_depuis_charge_precedente IS NOT NULL
              {where_veh}
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if rows and rows[0]["km_total"] is not None:
            return float(rows[0]["km_total"])
        return None

    def _energie_periode(self, veh_id: int = None, periode: str = "mois") -> float | None:
        """
        Énergie totale ajoutée (kWh) depuis le début de la période courante.
        Source : mv_charge_journee (énergie déjà agrégée par jour).

        periode : 'mois'  → depuis le 1er du mois courant
                  'annee' → depuis le 1er janvier de l'année courante

        Retourne None si aucune donnée sur la période.
        """
        trunc     = "month" if periode == "mois" else "year"
        ph        = self.ogEngine.placeholder
        params    = []
        where_veh = ""
        if veh_id is not None:
            where_veh = f"AND veh_id = {ph}"
            params.append(veh_id)

        sql = f"""
            SELECT ROUND(SUM(energie_ajoutee_kwh)::NUMERIC, 2) AS energie_totale
            FROM {self._SCHEMA}.{self._MV_JOURNEE}
            WHERE date_jour >= DATE_TRUNC('{trunc}', CURRENT_DATE)
              {where_veh}
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if rows and rows[0]["energie_totale"] is not None:
            return float(rows[0]["energie_totale"])
        return None

    def _conso_periode(self, veh_id: int = None, periode: str = "mois") -> float | None:
        """
        Consommation moyenne en kWh/100km depuis le début de la période courante.
        Source : mv_charge_journee.

        Calcul : SUM(energie_ajoutee_kwh) / SUM(miles * 1.60934) * 100
        Les jours sans distance sont exclus du numérateur ET du dénominateur.

        periode : 'mois'  → depuis le 1er du mois courant
                  'annee' → depuis le 1er janvier de l'année courante

        Retourne None si km_total = 0 ou aucune donnée.
        """
        trunc     = "month" if periode == "mois" else "year"
        ph        = self.ogEngine.placeholder
        params    = []
        where_veh = ""
        if veh_id is not None:
            where_veh = f"AND veh_id = {ph}"
            params.append(veh_id)

        sql = f"""
            SELECT
                SUM(energie_ajoutee_kwh)                        AS kwh_total,
                SUM(miles_depuis_charge_precedente) * 1.60934   AS km_total
            FROM {self._SCHEMA}.{self._MV_JOURNEE}
            WHERE date_jour >= DATE_TRUNC('{trunc}', CURRENT_DATE)
              AND miles_depuis_charge_precedente IS NOT NULL
              {where_veh}
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if not rows:
            return None
        kwh_total = rows[0].get("kwh_total")
        km_total  = rows[0].get("km_total")
        if not kwh_total or not km_total or float(km_total) == 0:
            return None
        return round(float(kwh_total) / float(km_total) * 100, 2)

    def energie_par_jour(
        self,
        veh_id    : int = None,
        date_debut: str = None,
    ) -> list[dict]:
        """
        Énergie ajoutée et km parcourus par jour depuis date_debut.
        Source : mv_journee (MV4) — couvre tous les jours avec snapshots,
        y compris les jours de conduite sans recharge.

        Retourne par jour :
            periode              — date_jour (DATE)
            energie_totale_kwh   — énergie ajoutée (kWh), NULL si pas de recharge
            km_journee           — km parcourus (déjà en km), NULL si pas de snapshot
        """
        ph         = self.ogEngine.placeholder
        params     = []
        where_veh  = ""
        where_date = ""
        if veh_id is not None:
            where_veh = f"AND veh_id = {ph}"
            params.append(veh_id)
        if date_debut is not None:
            where_date = f"AND date_jour >= {ph}"
            params.append(date_debut)

        sql = f"""
            SELECT
                date_jour               AS periode,
                energie_ajoutee_kwh     AS energie_totale_kwh,
                km_journee
            FROM {self._SCHEMA}.mv_journee
            WHERE TRUE
              {where_veh}
              {where_date}
            ORDER BY date_jour ASC
        """
        return self.ogEngine.execute_select(sql, params if params else None)

    def _derniere_capacite(self, veh_id: int = None) -> float | None:
        """
        Dernière capacité batterie estimée valide (non NULL).
        Retourne None si aucune estimation disponible en base.
        """
        ph        = self.ogEngine.placeholder
        params    = []
        where_veh = ""
        if veh_id is not None:
            where_veh = f"AND veh_id = {ph}"
            params.append(veh_id)

        sql = f"""
            SELECT capacite_estimee_kwh
            FROM {self._SCHEMA}.{self._MV}
            WHERE capacite_estimee_kwh IS NOT NULL
              {where_veh}
            ORDER BY fin_session DESC
            LIMIT 1
        """
        rows = self.ogEngine.execute_select(sql, params if params else None)
        if rows and rows[0]["capacite_estimee_kwh"] is not None:
            return float(rows[0]["capacite_estimee_kwh"])
        return None

    # =========================================================================
    # Helpers privés — construction des filtres
    # =========================================================================

    def _build_filtres(
        self,
        veh_id     : int  = None,
        date_debut : str  = None,
        date_fin   : str  = None,
        etat_final : str  = None,
    ) -> dict:
        """
        Normalise les paramètres nommés des méthodes publiques
        en dict de filtres compatible _build_where().

        Les valeurs None sont transmises telles quelles —
        _build_where() les ignore silencieusement.
        """
        return {
            "veh_id"               : veh_id,
            "debut_session__gte"   : date_debut,
            "debut_session__lte"   : date_fin,
            "etat_final"           : etat_final,
        }

    def _apply_computed(self, rows: list[dict]) -> list[dict]:
        """
        Applique les conversions post-agrégation définies dans _COLONNES_CALCULEES.

        Pour chaque colonne calculée :
            - vérifie que fn est callable AVANT de boucler sur les lignes
            - si non callable : log warning + colonne mise à None sur toutes
              les lignes — le controller peut intercepter None et avertir
              l'utilisateur. Une valeur miles non convertie silencieusement
              serait une faute grave (donnée fausse sans indication).
            - si callable et colonne source présente et non None → applique fn
            - si colonne source absente ou None → ignore silencieusement

        Les colonnes brutes sources sont conservées dans le dict résultat.
        Pas d'arrondi ici — précision maximale (défaut decimales=6 de miles_to_km).
        C'est le controller qui arrondit selon le besoin d'affichage.

        Exemple :
            row["odometer_debut"] = 63854.221895
            → row["odometer_debut_km"] = Tools.miles_to_km(63854.221895)
            →                          = 102766.942...  (6 décimales)
        """
        for col_calculee, (fn, col_source) in self._COLONNES_CALCULEES.items():

            # Vérification callable une seule fois par colonne, pas à chaque ligne
            if not callable(fn):
                self.ogLog.warning(
                    f"clsTstatCharge._apply_computed | "
                    f"'{col_calculee}' : la fonction associée n'est pas callable. "
                    f"Colonne mise à None sur toutes les lignes."
                )
                # None explicite sur toutes les lignes — le controller intercepte
                for row in rows:
                    row[col_calculee] = None
                continue

            for row in rows:
                valeur_source = row.get(col_source)
                if valeur_source is not None:
                    row[col_calculee] = fn(valeur_source)   # decimales=6 par défaut

        return rows