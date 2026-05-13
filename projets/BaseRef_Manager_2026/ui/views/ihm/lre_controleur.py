# ui/views/ihm/lre_controleur.py

from sysclasses.ui import QtControleur
from db.db_baseref.ihm.clsLRE import clsLRE


class LREControleur(QtControleur):
    """
    Contrôleur de la page Libellés de relation.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsLRE
    _ordre_tri     = clsLRE.LAN_ID