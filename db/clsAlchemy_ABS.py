"""
clsAlchemy_ABS.py
-----------------
Classe abstraite racine de toutes les entités SQLAlchemy V3.

Emplacement : db/clsAlchemy_ABS.py

Rôle :
    - Définit le contrat abstrait ctrl_valeurs() commun à toutes les classes C
    - Fournit les deux méthodes de chiffrement transparent (_get_decrypted,
      _set_encrypted) utilisées dans les mixins des colonnes chiffrées
    - N'hérite pas de clsDB_ABS — celui-ci est propre à EDFW
    - N'a pas d'__init__ — SQLAlchemy gère l'initialisation via DeclarativeBase
"""

#from abc import ABC, abstractmethod


class clsAlchemy_ABS():
    """
    Racine commune de toutes les classes C SQLAlchemy V3.
    Indépendante de tout SGBDR et de tout framework de présentation.
    """

    # ------------------------------------------------------------------
    # Contrat abstrait — obligatoire dans chaque classe C
    # ------------------------------------------------------------------
    def ctrl_valeurs(self) -> tuple[bool, str]:
        """
        Valide les règles métier avant INSERT/UPDATE.

        Retourne :
            (False, "")              — données valides, pas d'avertissement
            (False, "Avertissement") — données valides avec avertissement
            (True,  "ERREUR : ...")  — données invalides, opération bloquée
        """
        ...
        raise NotImplementedError(
            f"{self.__class__.__name__} doit implémenter ctrl_valeurs()"
        )