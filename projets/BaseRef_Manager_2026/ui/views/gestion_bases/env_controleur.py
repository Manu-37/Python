# ui/views/gestion_bases/env_controleur.py

from sysclasses.ui.qt import QtControleur
from db.db_baseref.public.clsENV import clsENV


class EnvControleur(QtControleur):
    """
    Contrôleur de la page Environnements.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsENV
    _ordre_tri     = clsENV.ENV_CODE