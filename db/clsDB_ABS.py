from abc import ABC, abstractmethod
from sysclasses.clsLOG import clsLOG


class clsDB_ABS(ABC) :
    """
    Classe de base générique socle commun entités + requêtes
      — indépendante de tout domaine métier.

    Fournit :
        - La connexion au moteur SQL via nom symbolique (clsDBAManager)
        - La construction dynamique de clauses WHERE avec paramètres
        - La génération d'expressions DATE_TRUNC pour granularité temporelle

    Ne connaît aucune table, aucune MV, aucun domaine.
    Les classes filles écrivent le SQL métier et utilisent ogEngine.execute_select().

    Usage :
        class clsChargeStats(clsDB_ABS):
            def __init__(self):
                super().__init__("TSTAT_DATA")
    """

    # Granularités supportées — clé française → valeur PostgreSQL DATE_TRUNC
    # 'semestre' est un cas spécial — DATE_TRUNC ne le supporte pas nativement,
    # _date_trunc génère une expression calculée ad hoc.
    _GRANULARITES: dict[str, str] = {
        "jour"      : "day",
        "semaine"   : "week",
        "mois"      : "month",
        "trimestre" : "quarter",
        "semestre"  : None,   # cas spécial — voir _date_trunc
        "annee"     : "year",
    }

    # --- Contrat de variables de classe ---

    @property
    @abstractmethod
    def _schema(self): pass

    @property
    @abstractmethod
    def _table(self): pass

    def __init__(self, db_symbolic_name: str):
        from sysclasses.clsDBAManager import clsDBAManager
        self.ogLog    = clsLOG()
        self.ogEngine = clsDBAManager().get_db(db_symbolic_name)

    # -------------------------------------------------------------------------
    # Construction dynamique de clauses WHERE
    # -------------------------------------------------------------------------

    def _build_where(self, filtres: dict) -> tuple[str, list]:
        """
        Construit une clause WHERE et la liste de paramètres associée
        depuis un dictionnaire de filtres.

        Opérateurs supportés dans les clés :
            "colonne"        → colonne = %s          (égalité)
            "colonne__gte"   → colonne >= %s         (supérieur ou égal)
            "colonne__lte"   → colonne <= %s         (inférieur ou égal)
            "colonne__gt"    → colonne > %s          (strictement supérieur)
            "colonne__lt"    → colonne < %s          (strictement inférieur)
            "colonne__in"    → colonne = ANY(%s)     (liste de valeurs)
            "colonne__null"  → colonne IS NULL       (valeur ignorée)
            "colonne__notnull" → colonne IS NOT NULL (valeur ignorée)

        Les filtres dont la valeur est None sont silencieusement ignorés,
        sauf pour __null et __notnull qui n'ont pas de valeur.

        Retourne :
            ("WHERE col1 = %s AND col2 >= %s", [val1, val2])
            ("", []) si aucun filtre actif

        Exemple :
            sql_where, params = self._build_where({
                "veh_id"         : 1,
                "debut_session__gte" : "2026-01-01",
                "debut_session__lte" : "2026-03-31",
                "etat_final__in" : ["Complete", "Stopped"],
            })
        """
        clauses = []
        params  = []
        ph      = self.ogEngine.placeholder

        for cle, valeur in filtres.items():

            # Décomposition clé → colonne + opérateur
            if "__" in cle:
                colonne, operateur = cle.rsplit("__", 1)
            else:
                colonne, operateur = cle, "eq"

            # Ignorer les filtres sans valeur (sauf IS NULL / IS NOT NULL)
            if valeur is None and operateur not in ("null", "notnull"):
                continue

            if operateur == "eq":
                clauses.append(f"{colonne} = {ph}")
                params.append(valeur)

            elif operateur == "gte":
                clauses.append(f"{colonne} >= {ph}")
                params.append(valeur)

            elif operateur == "lte":
                clauses.append(f"{colonne} <= {ph}")
                params.append(valeur)

            elif operateur == "gt":
                clauses.append(f"{colonne} > {ph}")
                params.append(valeur)

            elif operateur == "lt":
                clauses.append(f"{colonne} < {ph}")
                params.append(valeur)

            elif operateur == "in":
                clauses.append(f"{colonne} = ANY({ph})")
                params.append(list(valeur))

            elif operateur == "null":
                clauses.append(f"{colonne} IS NULL")

            elif operateur == "notnull":
                clauses.append(f"{colonne} IS NOT NULL")

            else:
                self.ogLog.warning(
                    f"clsDB_ABS._build_where | Opérateur inconnu ignoré : '{operateur}' "
                    f"sur colonne '{colonne}'"
                )

        if not clauses:
            return "", []

        return "WHERE " + " AND ".join(clauses), params

    # -------------------------------------------------------------------------
    # Génération d'expressions DATE_TRUNC
    # -------------------------------------------------------------------------

    def _date_trunc(self, granularite: str, colonne: str) -> str:
        """
        Retourne l'expression SQL DATE_TRUNC pour la granularité demandée.

        Paramètres :
            granularite : clé française — 'jour', 'semaine', 'mois',
                          'trimestre', 'annee'
            colonne     : nom de la colonne date/timestamp à tronquer

        Retourne :
            "DATE_TRUNC('month', debut_session)"

        Lève ValueError si la granularité n'est pas reconnue.

        Exemple :
            expr = self._date_trunc("mois", "debut_session")
            → "DATE_TRUNC('month', debut_session)"
        """
        if granularite not in self._GRANULARITES:
            valides = ", ".join(self._GRANULARITES.keys())
            raise ValueError(
                f"clsDB_ABS._date_trunc | Granularité '{granularite}' inconnue. "
                f"Valeurs acceptées : {valides}"
            )

        # Cas spécial : semestre — DATE_TRUNC ne supporte pas 'semester'
        # Semestre 1 = janvier→juin  → tronqué au 1er janvier
        # Semestre 2 = juillet→décembre → tronqué au 1er juillet
        if granularite == "semestre":
            return (
                f"DATE_TRUNC('year', {colonne}) + "
                f"INTERVAL '6 months' * "
                f"(CASE WHEN EXTRACT(MONTH FROM {colonne}) > 6 THEN 1 ELSE 0 END)"
            )

        pg_trunc = self._GRANULARITES[granularite]
        return f"DATE_TRUNC('{pg_trunc}', {colonne})"