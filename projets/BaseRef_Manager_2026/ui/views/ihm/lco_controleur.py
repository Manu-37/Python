# ui/views/ihm/lco_controleur.py

from sysclasses.ui import QtControleur
from db.db_baseref.ihm import clsLCO


class LCOControleur(QtControleur):
    """
    Contrôleur de la page Libelles colonnes.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsLCO
    _ordre_tri     = clsLCO.COL_ID+","+clsLCO.LAN_ID