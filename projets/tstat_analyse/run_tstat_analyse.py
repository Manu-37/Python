import sys
import os
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Résolution du chemin racine et ajout au sys.path
# ---------------------------------------------------------------------------
projet_racine = Path(__file__).resolve().parent
python_dir    = projet_racine.parent.parent   # remonte jusqu'à DEV/Python
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

# ---------------------------------------------------------------------------
# Constantes projet
# ---------------------------------------------------------------------------
PROJET_NOM = "tstat_analyse"
PROJET_VER = "0.0.1"

# ---------------------------------------------------------------------------
# Résolution du fichier ini — sans bootstrap, juste le chemin
# ---------------------------------------------------------------------------
from sysclasses.cste_chemins import init_chemins, get_app_dir
init_chemins(projet_racine, PROJET_NOM, PROJET_VER)

dossier_config = get_app_dir() / "config"
dossier_config.mkdir(exist_ok=True)
iniFile = dossier_config / "tstat_analyse.ini"

# Vérification minimale — inutile de lancer Streamlit si le .ini est absent
if not iniFile.exists():
    print(f"\n[ERREUR] Fichier de configuration introuvable :\n{iniFile}\n", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Transmission des constantes au subprocess Streamlit via os.environ.
# Le bootstrap réel se fait dans cache.py/_bootstrap() via st.cache_resource
# dans le processus Streamlit — c'est le seul qui compte.
# ---------------------------------------------------------------------------
env = os.environ.copy()
env["PYTHONPATH"]          = str(python_dir)
env["TSTAT_PROJET_RACINE"] = str(projet_racine)
env["TSTAT_PROJET_NOM"]    = PROJET_NOM
env["TSTAT_PROJET_VER"]    = PROJET_VER
env["TSTAT_INI_FILE"]      = str(iniFile)

# ---------------------------------------------------------------------------
# Lancement de Streamlit dans un subprocess séparé
# ---------------------------------------------------------------------------
accueil  = str(projet_racine / "Accueil.py")
commande = [
    sys.executable,
    "-m", "streamlit", "run",
    accueil,
    "--server.headless", "false",
]

try:
    subprocess.run(commande, check=True, env=env)
except KeyboardInterrupt:
    pass
except subprocess.CalledProcessError as e:
    print(f"\n[tstat_analyse] Streamlit s'est arrêté avec le code {e.returncode}",
          file=sys.stderr)
    sys.exit(e.returncode)