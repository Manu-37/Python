from abc import ABC, abstractmethod
from sysclasses.clsCrypto import clsCrypto
from sysclasses.exceptions import ErreurValidationBloquante, AvertissementValidation
from db.clsTableMetadata import clsTableMetadata


class clsEntity_ABS(ABC):
    """
    Classe abstraite socle de toutes les entités métier.
    Les classes filles DOIVENT définir : _schema, _table, _pk, ctrl_valeurs().
    Les singletons ogLog, ogEngine, ogManager sont injectés par clsBaseRef.

    Contrat de validation :
        ctrl_valeurs() est le juge de paix unique — appelé systématiquement
        dans insert() et update(), quelle que soit l'origine de l'appel
        (UI, script de maintenance, traitement par lot...).
        Impossible de contourner la validation en passant par les classes métier.

        Deux niveaux de retour :
            flag_error=True  → ErreurValidationBloquante — opération interdite
            flag_error=False, libelle non vide → AvertissementValidation — opération autorisée
    """

    # --- Contrat de variables de classe ---

    @property
    @abstractmethod
    def _schema(self): pass

    @property
    @abstractmethod
    def _table(self): pass

    @property
    @abstractmethod
    def _pk(self): pass

    @abstractmethod
    def ctrl_valeurs(self) -> tuple[bool, str]: pass

    # --- Initialisation ---

    def __init__(self, **kwargs):
        self._data          = {}
        self._data_original = {}
        self._oltable_metadata: clsTableMetadata = None
        self.oCrypto = clsCrypto()

        if kwargs:
            pk = self._pk
            if isinstance(pk, list):
                pk_present = all(k in kwargs for k in pk)
            else:
                pk_present = pk in kwargs

            if pk_present and len(kwargs) > (len(pk) if isinstance(pk, list) else 1):
                self._map_data(kwargs)
            else:
                self.ChargerDonnees(kwargs)

    # --- Mapping ---

    def _map_data(self, data: dict):
        """
        Remplit l'entité avec un dictionnaire de données (depuis SQL).
        _data          : valeurs courantes — modifiées par les setters
        _data_original : snapshot immuable — jamais touché après le chargement
                         sert de référence pour le WHERE de l'UPDATE
                         et pour détecter les colonnes réellement modifiées
        """
        self._data          = dict(data)
        self._data_original = dict(data)
        self.ogLog.debug(f"Objet {self.__class__.__name__} mappé ({len(data)} colonnes).")

    # --- Chargement ---

    def ChargerDonnees(self, criteres: dict):
        """
        Charge une ligne depuis la base selon des critères (PK simple ou composite).
        Ex: criteres = {'env_id': 1}
        Ex: criteres = {'bas_id': 1, 'env_id': 2}
        """
        clauses = [f"{col} = {self.ogEngine.placeholder}" for col in criteres.keys()]
        where_clause = " AND ".join(clauses)
        valeurs = tuple(criteres.values())

        sql = (
            f"SELECT * FROM {self.__class__._schema}.{self.__class__._table}"
            f" WHERE {where_clause}"
        )
        res = self.ogEngine.execute_select(sql, valeurs)

        if res:
            self._map_data(res[0])
        else:
            self.ogLog.warning(
                f"{self.__class__.__name__} : aucune ligne trouvée pour {criteres}"
            )

    # --- Chargement de masse ---

    @classmethod
    def load_all(cls, order_by: str = None) -> list[dict]:
        """
        Retourne toutes les lignes de la table sous forme de liste de dict.
        Utilisé par Entity_ListView pour alimenter la DataGrid.
        """
        from sysclasses.clsDBAManager import clsDBAManager
        engine = clsDBAManager().get_db(cls._DB_SYMBOLIC_NAME)

        sql = f"SELECT * FROM {cls._schema}.{cls._table}"
        if order_by:
            sql += f" ORDER BY {order_by}"

        return engine.execute_select(sql)

    @classmethod
    def get_metadata(cls) -> clsTableMetadata:
        """
        Retourne les métadonnées de la table (clsTableMetadata).
        Utilisé par Entity_ListView pour alimenter DataGrid (largeurs, cadrages).
        """
        from sysclasses.clsDBAManager import clsDBAManager
        engine = clsDBAManager().get_db(cls._DB_SYMBOLIC_NAME)
        return engine.get_table_metadata(schema=cls._schema, table=cls._table)

    # --- CRUD ---

    def insert(self):
        """
        Insère une nouvelle ligne.
        - Validation métier systématique via ctrl_valeurs() — impossible de contourner.
        - PK auto (SERIAL/IDENTITY) : exclue de l'INSERT, récupérée via RETURNING.
        - PK fournie : vérifiée avant insertion.
        - PK composite : chaque colonne PK doit être renseignée.
        """
        # Validation métier — garde-fou systématique
        # Protège aussi les insertions par lot et les scripts de maintenance
        flag_erreur, libelle_erreur = self.ctrl_valeurs()
        if flag_erreur:
            raise ErreurValidationBloquante(libelle_erreur)
        elif libelle_erreur:
            raise AvertissementValidation(libelle_erreur)

        metadata = self.TableMetadata
        pk_cols  = metadata.primary_keys
        auto_pk  = metadata.auto_increment_pk

        insert_cols = metadata.insertable_columns

        # Vérification PK manuelle si pas d'auto-increment
        if auto_pk is None:
            for col in pk_cols:
                if self._data.get(col) is None:
                    raise ValueError(f"La colonne PK '{col}' doit être fournie pour l'insert.")

        # Lecture directe de _data : les données y sont déjà dans leur état
        # final (chiffrées si nécessaire) depuis l'appel des setters.
        # On n'utilise pas getattr() qui passerait par les getters
        # et déchiffrerait les colonnes BYTEA avant envoi à la DB.
        values = [self._data.get(col) for col in insert_cols]

        returned = self.ogEngine.insert(
            schema=self.__class__._schema,
            table=self.__class__._table,
            columns=insert_cols,
            values=values,
            returning_columns=[auto_pk] if auto_pk else None
        )

        # Hydratation de la PK générée
        if auto_pk and returned:
            setattr(self, auto_pk, returned[0])

        if len(pk_cols) == 1:
            return getattr(self, pk_cols[0])
        else:
            return tuple(getattr(self, col) for col in pk_cols)

    def update(self):
        """
        Met à jour une ligne existante.
        - Validation métier systématique via ctrl_valeurs() — impossible de contourner.
        """
        # Validation métier — même garde-fou que insert()
        flag_erreur, libelle_erreur = self.ctrl_valeurs()
        if flag_erreur:
            raise ErreurValidationBloquante(libelle_erreur)
        elif libelle_erreur:
            raise AvertissementValidation(libelle_erreur)

        metadata = self.TableMetadata
        pk_cols  = metadata.primary_keys

        if not pk_cols:
            raise ValueError("Aucune PK définie — impossible d'effectuer un UPDATE.")

        # WHERE sur les valeurs originales — garantit qu'on met à jour
        # la bonne ligne même si les colonnes PK ont été modifiées (PK composite FK)
        where_conditions = {col: self._data_original.get(col) for col in pk_cols}

        if any(v is None for v in where_conditions.values()):
            raise ValueError("UPDATE impossible : PK originale incomplète.")

        # Détection des colonnes réellement modifiées.
        # On exclut les PK pures non-FK et les colonnes identity.
        all_cols = [
            col["name"] for col in metadata._metadata
            if not col["is_identity"]
            and not (col["is_pk"] and not col.get("is_fk"))
        ]

        update_cols = [
            col for col in all_cols
            if self._data.get(col) != self._data_original.get(col)
        ]

        if not update_cols:
            self.ogLog.debug(f"{self.__class__.__name__} : aucune modification détectée, UPDATE ignoré.")
            return None

        update_values = [self._data.get(col) for col in update_cols]
        self.ogLog.debug(f"{self.__class__.__name__} : UPDATE sur {update_cols}")

        result = self.ogEngine.update(
            schema=self.__class__._schema,
            table=self.__class__._table,
            columns=update_cols,
            values=update_values,
            where_conditions=where_conditions,
            returning_columns=pk_cols
        )

        # Après un UPDATE réussi, on resynchronise _data_original
        self._data_original = dict(self._data)
        return result

    def delete(self):
        metadata = self.TableMetadata
        pk_cols  = metadata.primary_keys

        # WHERE sur les valeurs originales — cohérent avec update()
        where_conditions = {col: self._data_original.get(col) for col in pk_cols}

        if any(v is None for v in where_conditions.values()):
            raise ValueError("DELETE impossible : PK incomplète.")

        return self.ogEngine.delete(
            schema=self.__class__._schema,
            table=self.__class__._table,
            where_conditions=where_conditions,
            returning_columns=pk_cols
        )

    # --- Accesseurs données ---

    def get_natural(self, nom_colonne: str):
        """Retourne la valeur brute (non chiffrée) depuis _data."""
        return self._data.get(nom_colonne)

    def set_natural(self, nom_colonne: str, valeur):
        """Stocke la valeur brute dans _data."""
        self._data[nom_colonne] = valeur

    def get_decrypted(self, nom_colonne: str) -> str:
        """Retourne la valeur déchiffrée (colonne BYTEA chiffrée en base)."""
        return self.oCrypto.decrypt(self._data.get(nom_colonne))

    def set_encrypted(self, nom_colonne: str, valeur: str):
        """Chiffre la valeur et la stocke dans _data."""
        self._data[nom_colonne] = self.oCrypto.encrypt(valeur)

    # --- Usine d'objets ---

    @classmethod
    def DepuisResultat(cls, resultats_sql: list[dict]):
        """Instancie une liste d'objets depuis un résultat SQL."""
        objets = []
        if resultats_sql:
            for row in resultats_sql:
                objets.append(cls(**dict(row)))
        return objets

    # --- Listes FK (pour ComboBox) ---

    def get_list_FK(self, col_name: str) -> list[tuple]:
        """
        Retourne la liste des choix pour un ComboBox FK.
        Retourne une liste de tuples : [(id, "label affiché"), ...]
        """
        metadata = self.TableMetadata
        col_meta = metadata.get_column(col_name)

        if not col_meta.get("is_fk"):
            raise ValueError(f"La colonne '{col_name}' n'est pas une FK.")

        fk_display = getattr(self.__class__, "FK_DISPLAY", {})
        display_cols = fk_display.get(col_name)

        if not display_cols:
            raise ValueError(
                f"FK_DISPLAY non déclaré pour '{col_name}' dans {self.__class__.__name__}."
            )

        fk_schema    = col_meta["fk_schema"]
        fk_table     = col_meta["fk_table"]
        fk_value_col = col_meta["fk_value_col"]
        order_col    = display_cols[0]

        select_cols = ", ".join([fk_value_col] + display_cols)

        sql = (
            f"SELECT {select_cols} "
            f"FROM {fk_schema}.{fk_table} "
            f"ORDER BY {order_col}"
        )

        rows = self.ogEngine.execute_select(sql)

        result = []
        for row in rows:
            valeur = row[fk_value_col]
            label  = " — ".join(str(row[col]) for col in display_cols)
            result.append((valeur, label))

        return result

    # --- Métadonnées (lazy) ---

    @property
    def TableMetadata(self) -> clsTableMetadata:
        if self._oltable_metadata is None:
            self._oltable_metadata = self.ogEngine.get_table_metadata(
                schema=self._schema,
                table=self._table
            )
        return self._oltable_metadata