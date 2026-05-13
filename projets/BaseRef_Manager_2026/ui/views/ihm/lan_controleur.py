# ui/views/ihm/lan_controleur.py

from sysclasses.ui import QtControleur
from db.db_baseref.ihm.clsLAN import clsLAN


class LANControleur(QtControleur):
    """
    Contrôleur de la page Langues.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsLAN
    _ordre_tri     = clsLAN.LAN_ORDRE