# BaseRef_Manager_3.py

import sys
from pathlib import Path

# --- Calcul du chemin racine ---
projet_racine = Path(__file__).resolve().parent
python_dir    = projet_racine.parent.parent
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

# --- Constantes projet ---
PROJET_NOM = "BaseRef_Manager_3"
PROJET_VER = "0.0.1"

# --- Chemins ---
from sysclasses.cste_chemins import init_chemins, get_app_dir
init_chemins(projet_racine, PROJET_NOM, PROJET_VER)

dossier_config = get_app_dir() / "config"
dossier_config.mkdir(exist_ok=True)
fichier_ini = dossier_config / "BaseRef_Manager_3.ini"

# --- Bootstrap ---
from sysclasses.AppBootstrap import AppBootstrap
from clsINIBaseRef_Manager_3 import clsINIBaseRef_Manager_3
bootstrap = AppBootstrap(fichier_ini, clsINIBaseRef_Manager_3, mode='console')

# Après le bootstrap, avant l'engine SQLAlchemy
from sysclasses.clsDBAManager import clsDBAManager
dba = clsDBAManager()
conn = dba.get_db("__REGISTRY__")

# Port local du tunnel SSH
if conn._ssh_tunnel:
    print(f"Port tunnel SSH : {conn._ssh_tunnel.local_bind_port}")
    input()
else:
    print("Connexion directe — pas de tunnel SSH")

# --- SQLAlchemy ---
from sqlalchemy import create_engine, text
from sysclasses.clsDBAManager import clsDBAManager

conn_psycopg2 = clsDBAManager().get_db("__REGISTRY__")._connection

engine = create_engine(
    "postgresql+psycopg2://",
    creator=lambda: conn_psycopg2
)

# --- Test ---
with engine.connect() as conn:
    result = conn.execute(text("SELECT lan_id, lan_code, lan_nom FROM ihm.t_langue_lan"))
    for row in result:
        print(row.lan_id, row.lan_code, row.lan_nom)