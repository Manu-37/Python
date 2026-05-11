# ui/views/gestion_bases/bas_env_controleur.py

from sysclasses.ui.qt import QtControleur
from db.db_baseref.public.clsBAS_ENV_NBE import clsBAS_ENV_NBE


class BasEnvControleur(QtControleur):
    """
    Contrôleur de la page Paramétrages bases/env.
    La fiche s'ouvre dans un onglet externe (on_ouvrir_fiche injecté par MainWindow).
    Pas de zone basse intégrée (_avec_fiche = False).
    """
    _classe_entite = clsBAS_ENV_NBE
    _ordre_tri     = clsBAS_ENV_NBE.BAS_ID
    _avec_fiche    = False