# ui/views/Tesla/TTK_Cntroleur.py

from sysclasses.ui.qt import QtControleur
from db.db_tstat_admin.public.clsTTK import clsTTK


class TTKControleur(QtControleur):
    """
    Contrôleur de la page Jeton Token.
    La fiche s'ouvre dans un onglet externe (on_ouvrir_fiche injecté par MainWindow).
    Pas de zone basse intégrée (_avec_fiche = False).
    """
    _classe_entite = clsTTK
    _ordre_tri     = clsTTK.VEH_ID
    _avec_fiche    = False