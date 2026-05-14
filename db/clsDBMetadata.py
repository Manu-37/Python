from sysclasses.clsLOG        import clsLOG
from sysclasses.clsDBAManager import clsDBAManager


class clsDBMetadata:
    """
    Enrichit clsTableMetadata depuis le référentiel IHM (ihm.v_col + t_libelle_relation_lre).
    Instancié par clsTableMetadata dans son __init__ — jamais directement.
    Si aucune donnée référentiel n'existe pour la table demandée, est_disponible vaut False.
    """

    # Constantes IHM — noms de schéma/tables en Python, jamais en dur dans le SQL
    _SCH     = "ihm"
    _SCH_PUB = "public"
    _T_BAS   = "t_base_bas"
    _T_DB    = "t_db_db"
    _T_LAN   = "t_langue_lan"
    _T_REL   = "t_relation_rel"
    _T_LRE   = "t_libelle_relation_lre"
    _V_COL   = "v_col"

    def __init__(self, db_symbolic_name: str, rel_nom: str):
        self._disponible = False
        self._colonnes   = {}   # col_nom → {lco_label, lco_label_court, lco_tooltip, col_largeur, taf_code}
        self._relation   = None # {lre_label, lre_tooltip}

        try:
            self._log    = clsLOG()
            self._engine = clsDBAManager().get_db("__REGISTRY__")
            ph           = self._engine.placeholder

            db_id = self._resoudre_db_id(ph, db_symbolic_name)
            if db_id is None:
                return

            lan_id = self._resoudre_langue(ph)
            if lan_id is None:
                return

            self._charger_colonnes(ph, db_id, rel_nom, lan_id)

            if not self._colonnes:
                return

            rel_id = self._resoudre_relation(ph, db_id, rel_nom)
            if rel_id is not None:
                self._charger_relation(ph, rel_id, lan_id)

            self._disponible = True

        except Exception as e:
            self._log.debug(
                f"clsDBMetadata | {db_symbolic_name}.{rel_nom} — référentiel indisponible : {e}"
            )

    # ------------------------------------------------------------------
    # Propriétés publiques
    # ------------------------------------------------------------------

    @property
    def est_disponible(self) -> bool:
        return self._disponible

    @property
    def colonnes(self) -> dict:
        return self._colonnes

    @property
    def relation(self) -> dict | None:
        return self._relation

    # ------------------------------------------------------------------
    # Résolution interne
    # ------------------------------------------------------------------

    def _resoudre_db_id(self, ph: str, db_symbolic_name: str) -> int | None:
        """Résout bas_nom (_DB_SYMBOLIC_NAME) → db_id via t_base_bas → t_db_db."""
        sql = (
            f"SELECT db.db_id "
            f"FROM {self._SCH}.{self._T_DB} db "
            f"JOIN {self._SCH_PUB}.{self._T_BAS} bas ON bas.bas_id = db.bas_id "
            f"WHERE bas.bas_nom = {ph} "
            f"FETCH FIRST 1 ROWS ONLY"
        )
        rows = self._engine.execute_select(sql, (db_symbolic_name,))
        return rows[0]["db_id"] if rows else None

    def _resoudre_langue(self, ph: str) -> int | None:
        sql  = (f"SELECT lan_id FROM {self._SCH}.{self._T_LAN} "
                f"ORDER BY lan_ordre FETCH FIRST 1 ROWS ONLY")
        rows = self._engine.execute_select(sql)
        return rows[0]["lan_id"] if rows else None

    def _charger_colonnes(self, ph: str, db_id: int, rel_nom: str, lan_id: int):
        sql = (
            f"SELECT col_nom, col_largeur, taf_code, "
            f"       lco_label, lco_label_court, lco_tooltip "
            f"FROM {self._SCH}.{self._V_COL} "
            f"WHERE db_id  = {ph} "
            f"  AND rel_nom = {ph} "
            f"  AND lan_id  = {ph} "
            f"  AND col_actif = TRUE"
        )
        rows = self._engine.execute_select(sql, (db_id, rel_nom, lan_id))
        for row in rows:
            self._colonnes[row["col_nom"]] = {
                "lco_label":       row.get("lco_label"),
                "lco_label_court": row.get("lco_label_court"),
                "lco_tooltip":     row.get("lco_tooltip"),
                "col_largeur":     row.get("col_largeur"),
                "taf_code":        row.get("taf_code"),
            }

    def _resoudre_relation(self, ph: str, db_id: int, rel_nom: str) -> int | None:
        sql = (
            f"SELECT rel.rel_id "
            f"FROM {self._SCH}.{self._T_REL} rel "
            f"JOIN {self._SCH}.t_schema_sch sch ON sch.sch_id = rel.sch_id "
            f"WHERE sch.db_id   = {ph} "
            f"  AND rel.rel_nom = {ph} "
            f"  AND rel.rel_actif = TRUE "
            f"FETCH FIRST 1 ROWS ONLY"
        )
        rows = self._engine.execute_select(sql, (db_id, rel_nom))
        if not rows:
            return None
        if len(rows) > 1:
            self._log.warning(
                f"clsDBMetadata | rel_nom '{rel_nom}' ambigu pour db_id={db_id} "
                f"— première occurrence retenue."
            )
        return rows[0]["rel_id"]

    def _charger_relation(self, ph: str, rel_id: int, lan_id: int):
        sql = (
            f"SELECT lre_label, lre_tooltip "
            f"FROM {self._SCH}.{self._T_LRE} "
            f"WHERE rel_id = {ph} AND lan_id = {ph}"
        )
        rows = self._engine.execute_select(sql, (rel_id, lan_id))
        if rows:
            self._relation = {
                "lre_label":   rows[0]["lre_label"],
                "lre_tooltip": rows[0]["lre_tooltip"],
            }
