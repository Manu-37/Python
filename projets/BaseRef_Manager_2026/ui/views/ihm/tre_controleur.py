# ui/views/ihm/tre_controleur.py

from sysclasses.ui import QtControleur
from db.db_baseref.ihm.clsTRE import clsTRE


class TREControleur(QtControleur):
    """
    Contrôleur de la page Types de relations.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsTRE
    _ordre_tri     = clsTRE.TRE_CODE