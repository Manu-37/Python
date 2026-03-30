import psycopg2
from sysclasses.clsDBA_SQL import clsDBA_SQL
from db.clsTableMetadata import clsTableMetadata

_TYPE_MAPPING = {
    # --- NUMERIC ---
    "smallint"                    : ("NUMERIC", "SMALLINT"),
    "integer"                     : ("NUMERIC", "INTEGER"),
    "bigint"                      : ("NUMERIC", "BIGINT"),
    "numeric"                     : ("NUMERIC", "DECIMAL"),
    "decimal"                     : ("NUMERIC", "DECIMAL"),
    "real"                        : ("NUMERIC", "FLOAT"),
    "double precision"            : ("NUMERIC", "DOUBLE"),
    "serial"                      : ("NUMERIC", "SERIAL"),
    "bigserial"                   : ("NUMERIC", "BIGSERIAL"),
    # --- STRING ---
    "character varying"           : ("STRING", "VARCHAR"),
    "varchar"                     : ("STRING", "VARCHAR"),
    "character"                   : ("STRING", "CHAR"),
    "char"                        : ("STRING", "CHAR"),
    "text"                        : ("STRING", "TEXT"),
    # --- BOOLEAN ---
    "boolean"                     : ("BOOLEAN", "BOOLEAN"),
    # --- TEMPORAL ---
    "date"                        : ("TEMPORAL", "DATE"),
    "timestamp without time zone" : ("TEMPORAL", "TIMESTAMP"),
    "timestamp with time zone"    : ("TEMPORAL", "TIMESTAMP_TZ"),
    "time"                        : ("TEMPORAL", "TIME"),
    "interval"                    : ("TEMPORAL", "INTERVAL"),
    # --- BINARY ---
    "bytea"                       : ("BINARY", "BYTEA"),
    # --- JSON ---
    "json"                        : ("JSON", "JSON"),
    "jsonb"                       : ("JSON", "JSONB"),
    # --- UUID ---
    "uuid"                        : ("UUID", "UUID"),
}


class clsSQL_Postgre(clsDBA_SQL):

    def __init__(self, log):
        super().__init__(log)

    # =========================================================================
    # Connexion
    # =========================================================================

    def connect(self, host, port, dbname, user, pwd):
        try:
            self._connection = psycopg2.connect(
                host=host, port=port, database=dbname, user=user, password=pwd
            )
            self._log.debug(f"SQL | Connexion établie : {dbname} sur {host}:{port}")
        except Exception as e:
            self._log.error(f"SQL | Échec connexion : {e}")
            raise

    def _get_cursor(self):
        if not self._connection:
            raise ConnectionError("Aucune connexion active.")
        return self._connection.cursor()

    def begin(self):
        if self._connection:
            self._log.debug("SQL | BEGIN")

    def commit(self):
        if self._connection:
            self._connection.commit()
            self._log.debug("SQL | COMMIT")

    def rollback(self):
        if self._connection:
            self._connection.rollback()
            self._log.warning("SQL | ROLLBACK")

    # =========================================================================
    # Métadonnées — méthodes publiques
    # =========================================================================

    def get_table_metadata(self, schema: str, table: str) -> clsTableMetadata:
        """
        Retourne les métadonnées complètes d'une TABLE :
        colonnes, types, PK, FK, identity, comments.
        Signature inchangée — aucune régression sur le code existant.
        """
        rows    = self.execute_select(self._sql_colonnes(), (schema, table))
        pk_set  = self._fetch_pk_set(schema, table)
        fk_map  = self._fetch_fk_map(schema, table)
        com_map = self._fetch_comment_map(schema, table)

        canonical_rows = self._build_metadata_columns(
            rows    = rows,
            pk_set  = pk_set,
            fk_map  = fk_map,
            com_map = com_map,
        )

        self._log.debug(f"get_table_metadata | {schema}.{table} — {len(canonical_rows)} colonnes")
        return clsTableMetadata(table, canonical_rows)

    def get_view_metadata(self, schema: str, view: str) -> clsTableMetadata:
        """
        Retourne les métadonnées d'une VUE ou VUE MATÉRIALISÉE :
        colonnes, types, comments.
        Pas de PK ni FK — non pertinents sur une vue.
        """
        rows    = self.execute_select(self._sql_colonnes(), (schema, view))
        com_map = self._fetch_comment_map(schema, view)

        canonical_rows = self._build_metadata_columns(
            rows    = rows,
            pk_set  = set(),    # vide — pas de PK sur une vue
            fk_map  = {},       # vide — pas de FK sur une vue
            com_map = com_map,
        )

        self._log.debug(f"get_view_metadata | {schema}.{view} — {len(canonical_rows)} colonnes")
        return clsTableMetadata(view, canonical_rows)

    # =========================================================================
    # Métadonnées — méthodes privées
    # =========================================================================

    def _sql_colonnes(self) -> str:
        """
        Requête information_schema commune tables et vues/MV.
        Retourne les colonnes structurelles — sans PK, FK ni comments
        (traités séparément pour tables ; absents pour vues).
        """
        return """
            SELECT
                c.column_name,
                c.data_type,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.is_nullable,
                c.column_default,
                c.is_identity,
                c.identity_generation,
                c.ordinal_position
            FROM information_schema.columns c
            WHERE c.table_schema = %s
              AND c.table_name   = %s
            ORDER BY c.ordinal_position
        """

    def _fetch_pk_set(self, schema: str, table: str) -> set:
        """
        Retourne le set des noms de colonnes PK via pg_catalog.
        pg_catalog n'a pas les restrictions de droits d'information_schema.
        """
        sql = """
            SELECT a.attname AS column_name
            FROM pg_constraint con
            JOIN pg_class     c  ON c.oid  = con.conrelid
            JOIN pg_namespace n  ON n.oid  = c.relnamespace
            JOIN pg_attribute a  ON a.attrelid = c.oid
                                AND a.attnum   = ANY(con.conkey)
            WHERE con.contype = 'p'
              AND n.nspname   = %s
              AND c.relname   = %s
        """
        rows = self.execute_select(sql, (schema, table))
        pk_set = {r["column_name"] for r in rows}
        self._log.debug(f"_fetch_pk_set | {schema}.{table} : {pk_set}")
        return pk_set

    def _fetch_fk_map(self, schema: str, table: str) -> dict:
        """
        Retourne un dict {col_locale: {fk_schema, fk_table, fk_value_col}}
        via pg_catalog — non filtré par les droits utilisateur.
        """
        sql = """
            SELECT
                kcu_local.column_name  AS col_locale,
                n_foreign.nspname      AS fk_schema,
                c_foreign.relname      AS fk_table,
                a_foreign.attname      AS fk_value_col
            FROM pg_constraint con
            JOIN pg_class     c_local   ON c_local.oid  = con.conrelid
            JOIN pg_namespace n_local   ON n_local.oid  = c_local.relnamespace
            JOIN information_schema.key_column_usage kcu_local
                                        ON kcu_local.constraint_name = con.conname
                                       AND kcu_local.table_schema    = n_local.nspname
                                       AND kcu_local.table_name      = c_local.relname
            JOIN pg_class     c_foreign ON c_foreign.oid = con.confrelid
            JOIN pg_namespace n_foreign ON n_foreign.oid = c_foreign.relnamespace
            JOIN pg_attribute a_foreign ON a_foreign.attrelid = con.confrelid
                                       AND a_foreign.attnum   = ANY(con.confkey)
            WHERE con.contype     = 'f'
              AND n_local.nspname = %s
              AND c_local.relname = %s
        """
        rows = self.execute_select(sql, (schema, table))
        fk_map = {
            r["col_locale"]: {
                "fk_schema"   : r["fk_schema"],
                "fk_table"    : r["fk_table"],
                "fk_value_col": r["fk_value_col"],
            }
            for r in rows
        }
        self._log.debug(f"_fetch_fk_map | {schema}.{table} : {fk_map}")
        return fk_map

    def _fetch_comment_map(self, schema: str, obj_name: str) -> dict:
        """
        Retourne un dict {ordinal_position: comment} depuis pg_catalog.
        Fonctionne pour tables, vues et vues matérialisées.
        col_description(oid, attnum) retourne NULL si pas de comment.
        """
        sql = """
            SELECT
                a.attnum                                    AS ordinal_position,
                col_description(c.oid, a.attnum)            AS comment
            FROM pg_class     c
            JOIN pg_namespace n  ON n.oid = c.relnamespace
            JOIN pg_attribute a  ON a.attrelid = c.oid
                                AND a.attnum > 0
                                AND NOT a.attisdropped
            WHERE n.nspname = %s
              AND c.relname = %s
            ORDER BY a.attnum
        """
        rows = self.execute_select(sql, (schema, obj_name))
        com_map = {r["ordinal_position"]: r["comment"] for r in rows}
        self._log.debug(f"_fetch_comment_map | {schema}.{obj_name} : {len(com_map)} comments")
        return com_map

    def _build_metadata_columns(self,
                                rows    : list[dict],
                                pk_set  : set,
                                fk_map  : dict,
                                com_map : dict) -> list[dict]:
        """
        Construit la liste canonical_rows alimentant clsTableMetadata.
        Code commun à get_table_metadata() et get_view_metadata().

        Paramètres :
            rows    : résultat information_schema.columns
            pk_set  : set des noms de colonnes PK (vide pour vues)
            fk_map  : dict col → infos FK            (vide pour vues)
            com_map : dict ordinal_position → comment (tables et vues)
        """
        canonical_rows = []

        for row in rows:
            is_identity = (
                row["is_identity"] == "YES"
                or (row["column_default"] and "nextval(" in row["column_default"])
            )

            col_name        = row["column_name"]
            ordinal         = row["ordinal_position"]
            fk_info         = fk_map.get(col_name)
            comment         = com_map.get(ordinal)

            canonical_rows.append({
                "name"                : col_name,
                "db_type"             : row["data_type"],
                "canonical_type"      : self.map_to_canonical(row["data_type"]),
                "max_length"          : row["character_maximum_length"],
                "precision"           : row["numeric_precision"],
                "scale"               : row["numeric_scale"],
                "nullable"            : row["is_nullable"] == "YES",
                "is_pk"               : col_name in pk_set,
                "is_identity"         : is_identity,
                "identity_generation" : row["identity_generation"],
                "default"             : row["column_default"],
                "comment"             : comment,
                # FK — None sur tous les champs si colonne non FK
                "is_fk"               : fk_info is not None,
                "fk_schema"           : fk_info["fk_schema"]    if fk_info else None,
                "fk_table"            : fk_info["fk_table"]     if fk_info else None,
                "fk_value_col"        : fk_info["fk_value_col"] if fk_info else None,
            })

        return canonical_rows

    # =========================================================================
    # CRUD
    # =========================================================================

    def insert(self, schema, table, columns, values, returning_columns=None):
        columns_sql  = ", ".join(columns)
        placeholders = ", ".join([self.placeholder] * len(columns))
        sql = f"INSERT INTO {schema}.{table} ({columns_sql}) VALUES ({placeholders})"

        if returning_columns:
            sql += f" RETURNING {', '.join(returning_columns)}"

        cursor = self._get_cursor()
        cursor.execute(sql, tuple(values))

        if returning_columns:
            return cursor.fetchone()
        return None

    def update(self, schema, table, columns, values,
               where_conditions: dict, returning_columns=None):
        if not columns:
            return None

        set_clause   = ", ".join(f"{col} = {self.placeholder}" for col in columns)
        where_clause = " AND ".join(f"{col} = {self.placeholder}" for col in where_conditions)

        sql = f"UPDATE {schema}.{table} SET {set_clause} WHERE {where_clause}"

        if returning_columns:
            returning_sql = ", ".join(returning_columns) if isinstance(returning_columns, (list, tuple)) else returning_columns
            sql += f" RETURNING {returning_sql}"

        cursor = self._get_cursor()
        cursor.execute(sql, tuple(values) + tuple(where_conditions.values()))

        if returning_columns:
            return cursor.fetchone()
        return None

    def delete(self, schema, table, where_conditions: dict, returning_columns=None):
        where_clause = " AND ".join(f"{col} = {self.placeholder}" for col in where_conditions)
        sql = f"DELETE FROM {schema}.{table} WHERE {where_clause}"

        if returning_columns:
            returning_sql = ", ".join(returning_columns) if isinstance(returning_columns, (list, tuple)) else returning_columns
            sql += f" RETURNING {returning_sql}"

        cursor = self._get_cursor()
        cursor.execute(sql, tuple(where_conditions.values()))

        if returning_columns:
            return cursor.fetchone()
        return None

    # =========================================================================
    # Propriétés et mapping
    # =========================================================================

    @property
    def placeholder(self) -> str:
        return "%s"

    @property
    def TYPE_MAPPING(self):
        return _TYPE_MAPPING

    def map_to_canonical(self, db_type: str):
        return self.TYPE_MAPPING.get(db_type.lower(), ("OTHER", db_type.upper()))