import sys
import os
from pathlib import Path

# --- Calcul du chemin racine du projet ---
projet_racine = Path(__file__).resolve().parent
python_dir = projet_racine.parent.parent  # remonte deux niveaux jusqu'à DEV/Python
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

# --- Constantes projet ---
PROJET_NOM = "BaseRef_Manager"
PROJET_VER = "0.3.0"

# --- INITIALISATION des chemins en PREMIER ---
# On appelle init_chemins() avant tout autre import sysclasses,
# garantissant que get_app_dir() / get_python_dir() / get_projet_nom() / get_projet_ver()
# retournent la bonne valeur pour tous les modules qui les appelleront ensuite.
from sysclasses.cste_chemins import init_chemins, get_app_dir
init_chemins(projet_racine, PROJET_NOM, PROJET_VER)

# --- Chemins dérivés ---
dossier_config = get_app_dir() / "config"
if not dossier_config.exists():
    os.mkdir(dossier_config)

iniFile = dossier_config / "BaseRef_Manager.ini"

# --- Bootstrap défensif des singletons ---
from sysclasses.AppBootstrap import AppBootstrap
from projets.BaseRef_Manager.clsINIBaseRef_Manager import clsINIBaseRef_Manager

bootstrap = AppBootstrap(iniFile, clsINIBaseRef_Manager)
# Si on arrive ici, les 5 singletons sont initialisés et fiables.
# bootstrap.oIni, bootstrap.oLog, bootstrap.oCrypto, bootstrap.oDB, bootstrap.oEmail
# sont accessibles ici si main() en a besoin.
# Partout ailleurs dans le code, les singletons se retrouvent
# via leur constructeur sans argument : clsLOG(), clsDBAManager(), etc.

# --- Lancement de l'UI ---
from ui.BaseRef_UICore import BaseRef_UICore


def main() -> None:
    app = BaseRef_UICore()
    app.mainloop()


if __name__ == "__main__":
    main()
