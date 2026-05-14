# baseref_manager_2026.py

import sys
from pathlib import Path

# --- Calcul du chemin racine ---
projet_racine = Path(__file__).resolve().parent
python_dir    = projet_racine.parent.parent
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

# --- Constantes projet ---
PROJET_NOM = "BaseRef_Manager_2026"
PROJET_VER = "0.2.0"

# --- Chemins ---
from sysclasses.cste_chemins import init_chemins, get_app_dir
init_chemins(projet_racine, PROJET_NOM, PROJET_VER)

dossier_config = get_app_dir() / "config"
dossier_config.mkdir(exist_ok=True)
fichier_ini = dossier_config / "BaseRef_Manager_2026.ini"

# --- QApplication EN PREMIER ---
# Doit exister avant tout widget Qt,
# et avant AppBootstrap en mode 'qt' (erreurs fatales via QMessageBox)
from PyQt6.QtWidgets import QApplication
from ui.theme import AppTheme
application_qt = QApplication(sys.argv)
AppTheme.apply(application_qt)

# --- Bootstrap ---
from sysclasses.AppBootstrap import AppBootstrap
from clsINIBaseRef_Manager_2026 import clsINIBaseRef_Manager_2026

bootstrap = AppBootstrap(fichier_ini, clsINIBaseRef_Manager_2026, mode='qt')

# --- Fenêtre principale ---
from ui.main_window import MainWindow
fenetre = MainWindow()
fenetre.show()

sys.exit(application_qt.exec())