from sysclasses.tools import Tools
from tstat_analyse.clsTstatBase import clsTstatBase


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

    _SCHEMA = "public"
    _MV     = "mv_charge_sessions_ext"

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
    # Helpers privés
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

        Pour chaque ligne et chaque colonne calculée :
            - si la colonne source est présente et non None → applique la fonction
            - si la colonne source est absente ou None      → ignore silencieusement

        Les colonnes brutes sources sont conservées dans le dict résultat.
        Les colonnes calculées sont ajoutées avec decimales=2 (données finales).

        Exemple :
            row["odometer_debut"] = 63854.22
            → row["odometer_debut_km"] = Tools.miles_to_km(63854.22, decimales=2)
        """
        for row in rows:
            for col_calculee, (fn, col_source) in self._COLONNES_CALCULEES.items():
                valeur_source = row.get(col_source)
                if valeur_source is not None:
                    row[col_calculee] = fn(valeur_source, decimales=2)
        return rows