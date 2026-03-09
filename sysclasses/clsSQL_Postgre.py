import psycopg2
from sysclasses.clsDBA_SQL import clsDBA_SQL
from db import clsTableMetadata
_TYPE_MAPPING = {
           # --- NUMERIC ---
            "smallint":      ("NUMERIC", "SMALLINT"),
            "integer":       ("NUMERIC", "INTEGER"),
            "bigint":        ("NUMERIC", "BIGINT"),
            "numeric":       ("NUMERIC", "DECIMAL"),
            "decimal":       ("NUMERIC", "DECIMAL"),
            "real":          ("NUMERIC", "FLOAT"),
            "double precision": ("NUMERIC", "DOUBLE"),
            "serial":        ("NUMERIC", "SERIAL"),
            "bigserial":     ("NUMERIC", "BIGSERIAL"),

            # --- STRING ---
            "character varying": ("STRING", "VARCHAR"),
            "varchar":       ("STRING", "VARCHAR"),
            "character":     ("STRING", "CHAR"),
            "char":          ("STRING", "CHAR"),
            "text":          ("STRING", "TEXT"),

            # --- BOOLEAN ---
            "boolean":       ("BOOLEAN", "BOOLEAN"),

            # --- TEMPORAL ---
            "date":          ("TEMPORAL", "DATE"),
            "timestamp without time zone": ("TEMPORAL", "TIMESTAMP"),
            "timestamp with time zone":    ("TEMPORAL", "TIMESTAMP_TZ"),
            "time":          ("TEMPORAL", "TIME"),
            "interval":      ("TEMPORAL", "INTERVAL"),

            # --- BINARY ---
            "bytea":         ("BINARY", "BYTEA"),

            # --- JSON ---
            "json":          ("JSON", "JSON"),
            "jsonb":         ("JSON", "JSONB"),

            # --- UUID ---
            "uuid":          ("UUID", "UUID"),
        }
class clsSQL_Postgre(clsDBA_SQL):
    def __init__(self, log):
        super().__init__(log)

    def connect(self, host, port, dbname, user, pwd):
        try:
            self._connection = psycopg2.connect(
                host=host, port=port, database=dbname, user=user, password=pwd
            )
            self._log.info(f"SQL | Connexion établie : {dbname} sur {host}:{port}")
        except Exception as e:
            self._log.error(f"SQL | Échec connexion : {e}")
            raise

    def _get_cursor(self):
        if not self._connection:
            raise ConnectionError("Aucune connexion active.")
        return self._connection.cursor()

    def begin(self):
        if self._connection: self._log.debug("SQL | BEGIN")

    def commit(self):
        if self._connection:
            self._connection.commit()
            self._log.info("SQL | COMMIT")

    def rollback(self):
        if self._connection:
            self._connection.rollback()
            self._log.warning("SQL | ROLLBACK")
     
    def get_table_metadata(self, schema: str, table: str):

        # --- Requête 1a : structure des colonnes (sans jointure PK) ---
        sql_colonnes = """
        SELECT
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.is_nullable,
            c.column_default,
            c.is_identity,
            c.identity_generation
        FROM information_schema.columns c
        WHERE c.table_schema = %s
        AND   c.table_name   = %s
        ORDER BY c.ordinal_position;
        """

        # --- Requête 1b : colonnes PK via pg_catalog ---
        # information_schema.table_constraints peut retourner vide si l'utilisateur
        # n'est pas propriétaire de la table. pg_catalog n'a pas cette restriction.
        sql_pk = """
        SELECT a.attname AS column_name
        FROM pg_constraint con
        JOIN pg_class c
            ON  c.oid = con.conrelid
        JOIN pg_namespace n
            ON  n.oid = c.relnamespace
        JOIN pg_attribute a
            ON  a.attrelid = c.oid
            AND a.attnum   = ANY(con.conkey)
        WHERE con.contype = 'p'
        AND   n.nspname   = %s
        AND   c.relname   = %s
        """

        # --- Requête 2 : FK de la table via pg_catalog ---
        # information_schema.constraint_column_usage est filtré par les droits
        # de l'utilisateur sur les tables cibles — peut retourner vide même si
        # les FK existent. pg_catalog n'a pas cette restriction.
        sql_fk = """
        SELECT
            kcu_local.column_name  AS col_locale,
            n_foreign.nspname      AS fk_schema,
            c_foreign.relname      AS fk_table,
            a_foreign.attname      AS fk_value_col
        FROM pg_constraint con
        JOIN pg_class c_local
            ON  c_local.oid = con.conrelid
        JOIN pg_namespace n_local
            ON  n_local.oid = c_local.relnamespace
        JOIN information_schema.key_column_usage kcu_local
            ON  kcu_local.constraint_name = con.conname
            AND kcu_local.table_schema    = n_local.nspname
            AND kcu_local.table_name      = c_local.relname
        JOIN pg_class c_foreign
            ON  c_foreign.oid = con.confrelid
        JOIN pg_namespace n_foreign
            ON  n_foreign.oid = c_foreign.relnamespace
        JOIN pg_attribute a_foreign
            ON  a_foreign.attrelid = con.confrelid
            AND a_foreign.attnum   = ANY(con.confkey)
        WHERE con.contype     = 'f'
        AND   n_local.nspname = %s
        AND   c_local.relname = %s
        """

        rows    = self.execute_select(sql_colonnes, (schema, table))
        pk_rows = self.execute_select(sql_pk, (schema, table))
        fk_rows = self.execute_select(sql_fk, (schema, table))

        # Set des colonnes PK pour lookup O(1)
        pk_set = {r["column_name"] for r in pk_rows}

        self._log.debug(f"PK set pour {schema}.{table} : {pk_set}")

        # Dict FK pour lookup O(1)
        fk_map = {
            r["col_locale"]: {
                "fk_schema":    r["fk_schema"],
                "fk_table":     r["fk_table"],
                "fk_value_col": r["fk_value_col"]
            }
            for r in fk_rows
        }

        self._log.debug(f"FK map pour {schema}.{table} : {fk_map}")

        canonical_rows = []

        for row in rows:

            is_identity = (
                row["is_identity"] == "YES"
                or (row["column_default"] and "nextval(" in row["column_default"])
            )

            col_name = row["column_name"]
            fk_info  = fk_map.get(col_name)  # None si pas FK

            canonical_rows.append({
                "name":               col_name,
                "db_type":            row["data_type"],
                "canonical_type":     self.map_to_canonical(row["data_type"]),
                "max_length":         row["character_maximum_length"],
                "precision":          row["numeric_precision"],
                "scale":              row["numeric_scale"],
                "nullable":           row["is_nullable"] == "YES",
                "is_pk":              col_name in pk_set,
                "is_identity":        is_identity,
                "identity_generation":row["identity_generation"],
                "default":            row["column_default"],
                # --- Infos FK (None si la colonne n'est pas une FK) ---
                "is_fk":              fk_info is not None,
                "fk_schema":          fk_info["fk_schema"]    if fk_info else None,
                "fk_table":           fk_info["fk_table"]     if fk_info else None,
                "fk_value_col":       fk_info["fk_value_col"] if fk_info else None,
            })

        return clsTableMetadata(table, canonical_rows)

    @property
    def placeholder(self) -> str:
        return "%s"

    def map_to_canonical(self, db_type: str):
        return self.TYPE_MAPPING.get(db_type.lower(),("OTHER", db_type.upper()))
        
    @property
    def TYPE_MAPPING(self):
        return _TYPE_MAPPING
    
    def insert(self, schema, table, columns, values, returning_columns=None):

        columns_sql = ", ".join(columns)
        placeholders = ", ".join([self.placeholder] * len(columns))

        sql = f"""
            INSERT INTO {schema}.{table}
            ({columns_sql})
            VALUES ({placeholders})
        """

        if returning_columns:
            returning_sql = ", ".join(returning_columns)
            sql += f" RETURNING {returning_sql}"

        cursor = self._get_cursor()
        cursor.execute(sql, tuple(values))

        if returning_columns:
            return cursor.fetchone()

        return None
    
    def update(self, schema, table, columns, values, where_conditions: dict, returning_columns=None):

        if not columns:
            return None

        set_clause = ", ".join(
            f"{col} = {self.placeholder}" for col in columns
        )

        where_clause = " AND ".join(
            f"{col} = {self.placeholder}" for col in where_conditions.keys()
        )

        sql = f"""
            UPDATE {schema}.{table}
            SET {set_clause}
            WHERE {where_clause}
        """

        if returning_columns:
            if isinstance(returning_columns, (list, tuple)):
                returning_sql = ", ".join(returning_columns)
            else:
                returning_sql = returning_columns

            sql += f" RETURNING {returning_sql}"

        cursor = self._get_cursor()

        params = tuple(values) + tuple(where_conditions.values())
        cursor.execute(sql, params)

        if returning_columns:
            return cursor.fetchone()

        return None

    def delete(self, schema, table, where_conditions: dict, returning_columns=None):

        where_clause = " AND ".join(
            f"{col} = {self.placeholder}" for col in where_conditions.keys()
        )

        sql = f"""
            DELETE FROM {schema}.{table}
            WHERE {where_clause}
        """

        if returning_columns:
            if isinstance(returning_columns, (list, tuple)):
                returning_sql = ", ".join(returning_columns)
            else:
                returning_sql = returning_columns

            sql += f" RETURNING {returning_sql}"

        cursor = self._get_cursor()
        cursor.execute(sql, tuple(where_conditions.values()))

        if returning_columns:
            return cursor.fetchone()

        return None