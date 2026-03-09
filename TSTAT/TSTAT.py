import sys
from pathlib import Path

# Setup du chemin pour le package SysClasses
PATH_ROOT = Path(__file__).resolve().parent.parent
if str(PATH_ROOT) not in sys.path:
    sys.path.insert(0, str(PATH_ROOT))

from SysClasses.clsLOG import clsLOG
from clsINITSTAT import clsINITSTAT

# Identité scellée du projet
PROJECT_NAME_AUTO = Path(__file__).stem 

APP_IDENTITY = {
    "PROJECT_NAME": PROJECT_NAME_AUTO,
    "VERSION": "0.0.1"
}

def main():
    path_ini = Path(__file__).resolve().parent / "config.ini"
    obj_log = None

    try:
        # 1. Chargement de la config spécialisée
        config = clsINITSTAT(str(path_ini))

        # 2. Préparation et lancement du Log
        log_setup = {
            "project_name": APP_IDENTITY["PROJECT_NAME"],
            "version": APP_IDENTITY["VERSION"],
            "level": config.log_level,
            "folder": config.log_folder,
            "max_bytes": config.log_max_bytes
        }
        obj_log = clsLOG(log_setup)
        
        obj_log.info(f"Environnement configuré : {config.env_type}")

        # 3. Récupération des paramètres DB (Prêt pour clsConnexionManager)
        db_params = config.get_db_params()
        obj_log.debug(f"Paramètres DB chargés pour le type: {db_params.get('type')}")

        obj_log.info("Ici commence la logique principale de l'application...")
        

    except Exception as e:
        if obj_log: obj_log.error(f"FATAL: {str(e)}")
        else: print(f"ERREUR INITIALISATION: {e}")
    
    finally:
        if obj_log: obj_log.finalize()

if __name__ == "__main__":
    main()