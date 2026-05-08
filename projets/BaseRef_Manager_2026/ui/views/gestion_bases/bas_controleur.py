# ui/views/gestion_bases/bas_controleur.py

from sysclasses.ui import QtControleur
from db.db_baseref.public.clsBAS import clsBAS


class BasControleur(QtControleur):
    """
    Contrôleur de la page Bases de données.
    Toute la logique générique est dans QtControleur.
    """
    _classe_entite = clsBAS
    _ordre_tri     = clsBAS.BAS_NOM