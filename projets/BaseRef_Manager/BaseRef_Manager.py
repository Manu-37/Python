import sys
import os
from pathlib import Path

# --- Calcul du chemin racine du projet ---
projet_racine = Path(__file__).resolve().parent
python_dir = projet_racine.parent.parent  # remonte deux niveaux jusqu'à DEV/Python
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

# --- INITIALISATION des chemins en PREMIER ---
# On appelle init_chemins() avant tout autre import sysclasses,
# garantissant que get_app_dir() / get_python_dir() retournent
# la bonne valeur pour tous les modules qui les appelleront ensuite.
from sysclasses.cste_chemins import init_chemins, get_app_dir, get_python_dir
init_chemins(projet_racine)

# --- Imports du framework (après init, ordre garanti) ---
from sysclasses import clsCrypto
from sysclasses import clsINICommun
from sysclasses import clsLOG
from sysclasses import clsDBAManager
from ui.BaseRef_UICore import BaseRef_UICore

# --- Chemins dérivés (lus via les fonctions, jamais via une copie) ---
dossier_config = get_app_dir() / "config"
if not dossier_config.exists():
    os.mkdir(dossier_config)

iniFile     = dossier_config / "BaseRef_Manager.ini"
dossier_log = get_python_dir() / "logs"


def main() -> None:
    ogIni      = clsINICommun(iniFile)
    ogLog      = clsLOG(ogIni)
    ogCrypto   = clsCrypto(ogIni.env_params['path'])
    ogDBEngine = clsDBAManager(ogIni)

    app = BaseRef_UICore()
    app.mainloop()


if __name__ == "__main__":
    main()
