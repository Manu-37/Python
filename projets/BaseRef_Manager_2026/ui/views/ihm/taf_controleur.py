# ui/views/ihm/taf_controleur.py

from sysclasses.ui import QtControleur
from db.db_baseref.ihm.clsTAF import clsTAF


class TAFControleur(QtControleur):
    """
    Contrôleur de la page Types de colonnes.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsTAF
    _ordre_tri     = clsTAF.TAF_CODE