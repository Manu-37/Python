# ui/views/ihm/tel_controleur.py

from sysclasses.ui import QtControleur
from db.db_baseref.ihm.clsTEL import clsTEL


class TELControleur(QtControleur):
    """
    Contrôleur de la page Types d'éléments graphique.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsTEL
    _ordre_tri     = clsTEL.TEL_CODE