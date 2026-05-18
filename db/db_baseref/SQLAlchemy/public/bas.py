"""
bas.py
------
Mixin métier pour t_base_bas (schéma public, base db_baseref).

Emplacement : db/db_baseref/SQLAlchemy/public/bas.py

Pattern T/C SQLAlchemy V3 :
    BASMixin est injecté dans TBaseBas par regenerer_modeles.py
    après chaque régénération :

        from db.db_baseref.SQLAlchemy.public.bas import BASMixin
        class TBaseBas(BASMixin, Base): ...

    TBaseBas devient ainsi la classe C finale — mapping SQLAlchemy
    complet + comportement métier. Aucune classe intermédiaire.

MRO : TBaseBas → BASMixin → clsAlchemy_ABS → Base → object

Pas de colonne chiffrée sur t_base_bas — tous les accès sont naturels.
Les colonnes chiffrées (nbe_host, nbe_user...) sont dans t_bas_env_nbe
et gérées par EncryptedBytes (TypeDecorator) dans le fichier généré.

Structure EDFW conservée :
    1. IDENTITÉ      — constantes de noms de colonnes
    2. NAISSANCE     — __init__ avec attributs de navigation lazy
    3. VALIDATION    — ctrl_valeurs() : tuple[bool, str]
    4. ACCÈS         — getters / setters avec noms qualifiés
    5. NAVIGATION    — alias lisibles sur les relations SQLAlchemy
"""

from db.clsAlchemy_ABS import clsAlchemy_ABS
from ..generated.db_baseref_generated import TBaseBas


class BASMixin(clsAlchemy_ABS):
    """
    Mixin métier pour t_base_bas.
    Injecté dans TBaseBas par regenerer_modeles.py après génération.
    Python pur — ne connaît pas SQLAlchemy directement.
    """

    # ------------------------------------------------------------------
    # 1. IDENTITÉ — constantes de noms de colonnes
    # ------------------------------------------------------------------
    BAS_ID          = "bas_id"
    BAS_NOM         = "bas_nom"
    BAS_DESCRIPTION = "bas_description"

    # ------------------------------------------------------------------
    # 2. NAISSANCE
    # ------------------------------------------------------------------
    def __init__(self, **kwargs):
        self._tab_nbe = None          # cache navigation lazy
        super().__init__(**kwargs)    # suit le MRO → SQLAlchemy s'initialise

    # ------------------------------------------------------------------
    # 3. VALIDATION
    # Reprise exacte des règles métier de clsBAS EDFW.
    # ------------------------------------------------------------------
    def ctrl_valeurs(self) -> tuple[bool, str]:
        erreurs    = []
        flag_error = False

        if not self.bas_nom:
            erreurs.append("ERREUR : Le nom symbolique de la base est obligatoire.")
            flag_error = True

        if self.bas_nom and not self.bas_nom.isupper():
            erreurs.append("Avertissement : Le nom symbolique de la base devrait être en majuscules.")

        if not self.bas_description:
            erreurs.append("ERREUR : La description de la base est obligatoire.")
            flag_error = True

        return flag_error, "\n".join(erreurs)

    # ------------------------------------------------------------------
    # 4. ACCÈS — getters / setters avec noms qualifiés
    # Noms identiques aux colonnes physiques — sans ambiguïté dans
    # toute la hiérarchie de classes (bas_description vs db_description
    # vs sch_description...).
    # ------------------------------------------------------------------

    @property
    def bas_id(self) -> int:
        return super().bas_id

    @property
    def bas_nom(self) -> str:
        return super().bas_nom

    @bas_nom.setter
    def bas_nom(self, valeur: str):
        super().bas_nom = valeur.strip().upper() if valeur else valeur

    @property
    def bas_description(self) -> str:
        return super().bas_description

    @bas_description.setter
    def bas_description(self, valeur: str):
        super().bas_description = valeur.strip() if valeur else valeur

    # ------------------------------------------------------------------
    # 5. NAVIGATION — alias lisibles sur les relations SQLAlchemy
    # t_bas_env_nbe est le nom généré par sqlacodegen.
    # ------------------------------------------------------------------

    @property
    def tab_nbe(self):
        """Noeuds de connexion liés à cette base (lazy via SQLAlchemy)."""
        return self.t_bas_env_nbe
    

class CBAS(BASMixin, TBaseBas):
    """
    Classe métier finale pour t_base_bas.
    Hérite du mixin métier et de la classe SQLAlchemy générée.
    """

    pass