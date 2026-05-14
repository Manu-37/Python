# services/explorateur_db.py

import json
from datetime import datetime, timezone

from sysclasses.clsLOG         import clsLOG
from sysclasses.clsDBAManager  import clsDBAManager
from db.db_baseref.ihm.clsDB   import clsDB
from db.db_baseref.ihm.clsSCH  import clsSCH
from db.db_baseref.ihm.clsREL  import clsREL
from db.db_baseref.ihm.clsCOL  import clsCOL
from db.db_baseref.ihm.clsDBR  import clsDBR


_TAF_MAP = {
    "NUMERIC":  "NUMERIQUE",
    "STRING":   "TEXTE",
    "BOOLEAN":  "BOOLEEN",
    "TEMPORAL": "DATE",
    "BINARY":   "BINAIRE",
    "JSON":     "TEXTE",
    "UUID":     "TEXTE",
}


class ExplorateurDB:
    """
    Service d'exploration différentielle d'une base de données.

    Flux normal :
        diff = explorateur.scanner()   # lit structure réelle, calcule diff, persiste DBR
        explorateur.valider(diff)      # importe les nouveautés, flagge les disparitions

    scanner() persiste toujours un rapport (clsDBR), même sans validation ultérieure.
    valider() peut être appelé plusieurs fois sur le même diff.
    """

    def __init__(self, oDb: clsDB):
        self._oDb      = oDb
        self._log      = clsLOG()
        self._bas_nom  = None   # résolu une fois à la première connexion
        self._env_code = None

    # =========================================================================
    # API publique
    # =========================================================================

    def scanner(self) -> dict:
        """
        Lit la structure réelle de la base, la compare au catalogue actif,
        persiste le rapport en DBR et retourne le dictionnaire diff.
        """
        structure = self._lire_structure_reelle()
        catalogue = self._lire_catalogue()
        diff      = self._calculer_diff(catalogue, structure)
        diff["db_id"]     = self._oDb.db_id
        diff["scan_date"] = datetime.now(timezone.utc).isoformat()
        self._persister_rapport(diff)
        return diff

    def valider(self, diff: dict):
        """
        Applique les modifications au catalogue BaseRef :
        - Nouveautés  → INSERT SCH / REL / COL avec commentaires comme amorce libellés
        - Disparitions → UPDATE *_actif = FALSE en cascade silencieuse sur les descendants
        """
        self._appliquer_nouveautes(diff.get("nouveautes", {}))
        self._appliquer_disparitions(diff.get("disparitions", {}))

    # =========================================================================
    # Connexion — délègue entièrement au clsDBAManager
    # =========================================================================

    def _get_engine(self):
        """
        Retourne le moteur de connexion vers la base explorée.
        Résout bas_nom une seule fois, puis délègue à clsDBAManager.get_db().
        Cas spécial '__REGISTRY__' : env non requis, connexion déjà dans le cache.
        """
        if self._bas_nom is None:
            from db.db_baseref.public.clsBAS import clsBAS
            oBas = clsBAS(bas_id=self._oDb.bas_id)
            if not oBas.bas_nom:
                raise RuntimeError(
                    f"Impossible de résoudre bas_id={self._oDb.bas_id}."
                )
            self._bas_nom = oBas.bas_nom
            if self._bas_nom != '__REGISTRY__':
                from db.db_baseref.public.clsENV import clsENV
                oEnv = clsENV(env_id=self._oDb.env_id)
                if not oEnv.env_code:
                    raise RuntimeError(
                        f"Impossible de résoudre env_id={self._oDb.env_id}."
                    )
                self._env_code = oEnv.env_code

        engine = clsDBAManager().get_db(self._bas_nom, env_type_test=self._env_code)
        if engine is None:
            raise RuntimeError(
                f"clsDBAManager ne peut pas établir la connexion "
                f"'{self._bas_nom}/{self._env_code}'."
            )
        return engine

    # =========================================================================
    # Lecture structure réelle
    # =========================================================================

    def _lire_structure_reelle(self) -> dict:
        """
        Retourne :
        {sch_nom: {rel_nom: {rel_type, colonnes: [...], nb_fk_ignorees: int}}}
        Les colonnes FK (is_fk=True) sont exclues — colonnes internes de jointure,
        sans valeur sémantique pour le catalogue IHM.
        """
        engine  = self._get_engine()
        result  = {}
        schemas = engine.list_schemas()

        for sch_nom in schemas:
            result[sch_nom] = {}
            relations = engine.list_relations(sch_nom)

            for rel in relations:
                rel_nom  = rel["rel_nom"]
                rel_type = rel["rel_type"]

                if rel_type == "MVIEW":
                    meta = engine.get_mview_metadata(sch_nom, rel_nom)
                elif rel_type == "VIEW":
                    meta = engine.get_view_metadata(sch_nom, rel_nom)
                else:
                    meta = engine.get_table_metadata(sch_nom, rel_nom)

                # Triplet = 3 derniers chars après le dernier '_'
                # Ex: t_schema_sch → "sch", mv_sessions_ses → "ses"
                # Si le dernier segment n'est pas 3 chars → pas de filtre
                parties = rel_nom.split("_")
                prefixe = parties[-1] if len(parties) >= 2 and len(parties[-1]) <= 3 else None

                colonnes    = []
                nb_ignorees = 0
                for col_nom in meta.columns:
                    info = meta.get_column(col_nom)
                    if prefixe and not col_nom.startswith(prefixe + "_"):
                        nb_ignorees += 1
                        continue
                    colonnes.append({
                        "col_nom":     col_nom,
                        "col_type":    info["canonical_type"][0],
                        "commentaire": info.get("comment"),
                    })

                if nb_ignorees:
                    self._log.debug(
                        f"_lire_structure_reelle | {sch_nom}.{rel_nom} : "
                        f"{nb_ignorees} colonne(s) ignorée(s) (hors triplet '{prefixe}')"
                    )

                result[sch_nom][rel_nom] = {
                    "rel_type":       rel_type,
                    "colonnes":       colonnes,
                    "nb_fk_ignorees": nb_ignorees,
                }

        return result

    # =========================================================================
    # Lecture catalogue
    # =========================================================================

    def _lire_catalogue(self) -> dict:
        """
        Retourne les éléments ACTIFS du catalogue pour ce db_id :
        {sch_nom: {sch_id, relations: {rel_nom: {rel_id, colonnes: {col_nom: col_id}}}}}
        """
        result  = {}
        schemas = clsSCH.load_all(
            where_clause=f"db_id = {self._oDb.db_id} AND sch_actif = TRUE"
        )

        for sch_row in schemas:
            sch_nom = sch_row[clsSCH.SCH_NOM]
            sch_id  = sch_row[clsSCH.SCH_ID]
            result[sch_nom] = {"sch_id": sch_id, "relations": {}}

            relations = clsREL.load_all(
                where_clause=f"sch_id = {sch_id} AND rel_actif = TRUE"
            )
            for rel_row in relations:
                rel_nom = rel_row[clsREL.REL_NOM]
                rel_id  = rel_row[clsREL.REL_ID]
                result[sch_nom]["relations"][rel_nom] = {"rel_id": rel_id, "colonnes": {}}

                colonnes = clsCOL.load_all(
                    where_clause=f"rel_id = {rel_id} AND col_actif = TRUE"
                )
                for col_row in colonnes:
                    col_nom = col_row[clsCOL.COL_NOM]
                    col_id  = col_row[clsCOL.COL_ID]
                    result[sch_nom]["relations"][rel_nom]["colonnes"][col_nom] = col_id

        return result

    # =========================================================================
    # Calcul du diff
    # =========================================================================

    def _calculer_diff(self, catalogue: dict, structure: dict) -> dict:
        """
        Diff à trois voies sur (sch_nom, rel_nom, col_nom).
        Une relation disparue est signalée sans détailler ses colonnes.
        """
        nouveautes   = {"schemas": [], "relations": [], "colonnes": []}
        disparitions = {"schemas": [], "relations": [], "colonnes": []}
        inchanges    = {"schemas": [], "relations": [], "colonnes": []}

        sch_reels = set(structure.keys())
        sch_cat   = set(catalogue.keys())

        for sch_nom in sch_reels - sch_cat:
            nouveautes["schemas"].append({"sch_nom": sch_nom})
            for rel_nom, rel_data in structure[sch_nom].items():
                nouveautes["relations"].append({
                    "sch_nom":        sch_nom,
                    "rel_nom":        rel_nom,
                    "rel_type":       rel_data["rel_type"],
                    "colonnes":       rel_data["colonnes"],
                    "nb_fk_ignorees": rel_data.get("nb_fk_ignorees", 0),
                })
                for col in rel_data["colonnes"]:
                    nouveautes["colonnes"].append(
                        {"sch_nom": sch_nom, "rel_nom": rel_nom, **col}
                    )

        for sch_nom in sch_cat - sch_reels:
            sch_data = catalogue[sch_nom]
            disparitions["schemas"].append(
                {"sch_id": sch_data["sch_id"], "sch_nom": sch_nom}
            )
            for rel_nom, rel_data in sch_data["relations"].items():
                disparitions["relations"].append(
                    {"rel_id": rel_data["rel_id"], "rel_nom": rel_nom, "sch_nom": sch_nom}
                )

        for sch_nom in sch_reels & sch_cat:
            inchanges["schemas"].append({"sch_nom": sch_nom})

            rel_reels = set(structure[sch_nom].keys())
            rel_cat   = set(catalogue[sch_nom]["relations"].keys())

            for rel_nom in rel_reels - rel_cat:
                rel_data = structure[sch_nom][rel_nom]
                nouveautes["relations"].append({
                    "sch_nom":        sch_nom,
                    "rel_nom":        rel_nom,
                    "rel_type":       rel_data["rel_type"],
                    "colonnes":       rel_data["colonnes"],
                    "nb_fk_ignorees": rel_data.get("nb_fk_ignorees", 0),
                })
                for col in rel_data["colonnes"]:
                    nouveautes["colonnes"].append(
                        {"sch_nom": sch_nom, "rel_nom": rel_nom, **col}
                    )

            for rel_nom in rel_cat - rel_reels:
                rel_data = catalogue[sch_nom]["relations"][rel_nom]
                disparitions["relations"].append(
                    {"rel_id": rel_data["rel_id"], "rel_nom": rel_nom, "sch_nom": sch_nom}
                )

            for rel_nom in rel_reels & rel_cat:
                inchanges["relations"].append({"sch_nom": sch_nom, "rel_nom": rel_nom})

                col_reels = {c["col_nom"] for c in structure[sch_nom][rel_nom]["colonnes"]}
                col_cat   = set(catalogue[sch_nom]["relations"][rel_nom]["colonnes"].keys())

                for col_nom in col_reels - col_cat:
                    col_info = next(
                        c for c in structure[sch_nom][rel_nom]["colonnes"]
                        if c["col_nom"] == col_nom
                    )
                    nouveautes["colonnes"].append(
                        {"sch_nom": sch_nom, "rel_nom": rel_nom, **col_info}
                    )

                for col_nom in col_cat - col_reels:
                    col_id = catalogue[sch_nom]["relations"][rel_nom]["colonnes"][col_nom]
                    disparitions["colonnes"].append({
                        "col_id":  col_id,
                        "col_nom": col_nom,
                        "rel_nom": rel_nom,
                        "sch_nom": sch_nom,
                    })

                for col_nom in col_reels & col_cat:
                    inchanges["colonnes"].append({
                        "sch_nom": sch_nom, "rel_nom": rel_nom, "col_nom": col_nom
                    })

        return {
            "nouveautes":   nouveautes,
            "disparitions": disparitions,
            "inchanges":    inchanges,
        }

    # =========================================================================
    # Persistance du rapport
    # =========================================================================

    def _persister_rapport(self, diff: dict):
        oDBR          = clsDBR()
        oDBR.db_id    = self._oDb.db_id
        oDBR.dbr_date = datetime.now(timezone.utc)
        oDBR.dbr_json = json.dumps(diff)
        oDBR.insert()
        oDBR.ogEngine.commit()
        self._log.info(
            f"ExplorateurDB | Rapport DBR persisté pour db_id={self._oDb.db_id}"
        )

    # =========================================================================
    # Application des nouveautés
    # =========================================================================

    def _appliquer_nouveautes(self, nouveautes: dict):
        from db.db_baseref.ihm.clsTRE import clsTRE
        from db.db_baseref.ihm.clsTAF import clsTAF

        sch_ids = {}   # sch_nom → sch_id (pour résolution dans les boucles suivantes)
        rel_ids = {}   # (sch_nom, rel_nom) → rel_id

        for sch_data in nouveautes.get("schemas", []):
            sch_nom        = sch_data["sch_nom"]
            oSCH           = clsSCH()
            oSCH.db_id     = self._oDb.db_id
            oSCH.sch_nom   = sch_nom
            oSCH.sch_actif = True
            oSCH.insert()
            oSCH.ogEngine.commit()
            sch_ids[sch_nom] = oSCH.sch_id

        for rel_data in nouveautes.get("relations", []):
            sch_nom = rel_data["sch_nom"]
            sch_id  = self._resoudre_sch_id(sch_nom, sch_ids)
            oTRE    = clsTRE(tre_code=rel_data["rel_type"])
            oREL           = clsREL()
            oREL.sch_id    = sch_id
            oREL.tre_id    = oTRE.tre_id
            oREL.rel_nom   = rel_data["rel_nom"]
            oREL.rel_actif = True
            oREL.insert()
            oREL.ogEngine.commit()
            rel_ids[(sch_nom, rel_data["rel_nom"])] = oREL.rel_id
            self._amorcer_libelles_rel(oREL, rel_data["rel_nom"])

        for col_data in nouveautes.get("colonnes", []):
            sch_nom = col_data["sch_nom"]
            rel_nom = col_data["rel_nom"]
            rel_id  = self._resoudre_rel_id(sch_nom, rel_nom, sch_ids, rel_ids)
            oTAF    = clsTAF(taf_code=_TAF_MAP.get(col_data["col_type"], "AUTO"))
            oCOL           = clsCOL()
            oCOL.rel_id    = rel_id
            oCOL.taf_id    = oTAF.taf_id
            oCOL.col_nom   = col_data["col_nom"]
            oCOL.col_actif = True
            oCOL.insert()
            oCOL.ogEngine.commit()
            self._amorcer_libelles_col(oCOL, col_data["col_nom"], col_data.get("commentaire"))

    def _amorcer_libelles_rel(self, oREL: clsREL, rel_nom: str):
        """
        Crée un LRE pour la première langue active uniquement.
        Le coalesce sur les autres langues est géré par le mécanisme applicatif.
        """
        from db.db_baseref.ihm.clsLRE import clsLRE
        from db.db_baseref.ihm.clsLAN import clsLAN
        langues = clsLAN.load_all(where_clause="lan_actif = TRUE", order_by="lan_ordre")
        if not langues:
            return
        lan_row        = langues[0]
        oLRE           = clsLRE()
        oLRE.rel_id    = oREL.rel_id
        oLRE.lan_id    = lan_row[clsLAN.LAN_ID]
        oLRE.lre_label = rel_nom[:128]
        oLRE.insert()
        oLRE.ogEngine.commit()

    def _amorcer_libelles_col(self, oCOL: clsCOL, col_nom: str, commentaire: str | None):
        """
        Crée un LCO par langue active.
        Convention commentaire PostgreSQL : "court|description longue"
          → label_court = partie gauche (≤15), label = partie gauche (≤128), tooltip = partie droite
        Sans commentaire : col_nom comme fallback sur label et label_court.
        """
        from db.db_baseref.ihm.clsLCO import clsLCO
        from db.db_baseref.ihm.clsLAN import clsLAN

        if commentaire and "|" in commentaire:
            parties     = commentaire.split("|", 1)
            label_court = parties[0].strip()[:15]
            label       = parties[0].strip()[:128]
            tooltip     = parties[1].strip() or None
        elif commentaire:
            label_court = col_nom[:15]
            label       = commentaire[:128]
            tooltip     = commentaire
        else:
            label_court = col_nom[:15]
            label       = col_nom[:128]
            tooltip     = None

        langues = clsLAN.load_all(where_clause="lan_actif = TRUE", order_by="lan_ordre")
        if not langues:
            return
        lan_row              = langues[0]
        oLCO                 = clsLCO()
        oLCO.col_id          = oCOL.col_id
        oLCO.lan_id          = lan_row[clsLAN.LAN_ID]
        oLCO.lco_label       = label
        oLCO.lco_label_court = label_court
        oLCO.lco_tooltip     = tooltip
        oLCO.insert()
        oLCO.ogEngine.commit()

    # =========================================================================
    # Application des disparitions
    # =========================================================================

    def _appliquer_disparitions(self, disparitions: dict):
        """
        Cascade silencieuse : UPDATE *_actif = FALSE sur les entités disparues
        et leurs descendants. Utilise execute_non_query pour efficacité.
        """
        engine = clsDBAManager().get_db('__REGISTRY__')
        sc     = clsSCH._schema

        for col_data in disparitions.get("colonnes", []):
            engine.execute_non_query(
                f"UPDATE {sc}.{clsCOL._table} SET col_actif = FALSE WHERE col_id = %s",
                (col_data["col_id"],)
            )

        for rel_data in disparitions.get("relations", []):
            rel_id = rel_data["rel_id"]
            engine.execute_non_query(
                f"UPDATE {sc}.{clsCOL._table} SET col_actif = FALSE WHERE rel_id = %s",
                (rel_id,)
            )
            engine.execute_non_query(
                f"UPDATE {sc}.{clsREL._table} SET rel_actif = FALSE WHERE rel_id = %s",
                (rel_id,)
            )

        for sch_data in disparitions.get("schemas", []):
            sch_id = sch_data["sch_id"]
            engine.execute_non_query(
                f"""UPDATE {sc}.{clsCOL._table} SET col_actif = FALSE
                    WHERE rel_id IN (
                        SELECT rel_id FROM {sc}.{clsREL._table} WHERE sch_id = %s
                    )""",
                (sch_id,)
            )
            engine.execute_non_query(
                f"UPDATE {sc}.{clsREL._table} SET rel_actif = FALSE WHERE sch_id = %s",
                (sch_id,)
            )
            engine.execute_non_query(
                f"UPDATE {sc}.{clsSCH._table} SET sch_actif = FALSE WHERE sch_id = %s",
                (sch_id,)
            )

        engine.commit()

    # =========================================================================
    # Résolution d'IDs — via instantiation directe (ChargerDonnees)
    # =========================================================================

    def _resoudre_sch_id(self, sch_nom: str, sch_ids: dict) -> int | None:
        """sch_ids contient les schémas fraîchement insérés ; sinon lecture DB."""
        if sch_nom in sch_ids:
            return sch_ids[sch_nom]
        oSCH = clsSCH(db_id=self._oDb.db_id, sch_nom=sch_nom)
        return oSCH.sch_id

    def _resoudre_rel_id(self, sch_nom: str, rel_nom: str,
                         sch_ids: dict, rel_ids: dict) -> int | None:
        """rel_ids contient les relations fraîchement insérées ; sinon lecture DB."""
        key = (sch_nom, rel_nom)
        if key in rel_ids:
            return rel_ids[key]
        sch_id = self._resoudre_sch_id(sch_nom, sch_ids)
        oREL   = clsREL(sch_id=sch_id, rel_nom=rel_nom)
        return oREL.rel_id
