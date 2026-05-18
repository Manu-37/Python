"""
testBas.py
----------
Test du pattern T/C SQLAlchemy V3 sur t_base_bas.
Affiche les bases enregistrées dans public.t_base_bas.

Emplacement : projets/BaseRef_Manager_3/Tools/testBas.py
"""

import sys
from pathlib import Path

TOOLS_DIR  = Path(__file__).resolve().parent
PROJET_DIR = TOOLS_DIR.parent
PYTHON_DIR = PROJET_DIR.parent.parent

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

# ---------------------------------------------------------------------------
# Bootstrap standard
# ---------------------------------------------------------------------------
from sysclasses.cste_chemins import init_chemins
init_chemins(PROJET_DIR, "BaseRef_Manager_3", "0.0.1")

fichier_ini = PROJET_DIR / "config" / "BaseRef_Manager_3.ini"

from sysclasses.AppBootstrap import AppBootstrap
from sysclasses.clsLOG import clsLOG
from projets.BaseRef_Manager_3.clsINIBaseRef_Manager_3 import clsINIBaseRef_Manager_3

bootstrap = AppBootstrap(fichier_ini, clsINIBaseRef_Manager_3, mode="console")
log = clsLOG()

# ---------------------------------------------------------------------------
# Connexion SQLAlchemy via tunnel existant
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sysclasses.clsDBAManager import clsDBAManager

registry = clsDBAManager().get_db("__REGISTRY__")

engine = create_engine(
    "postgresql+psycopg2://",
    creator=lambda: registry._connection
)

# ---------------------------------------------------------------------------
# Test CBAS
# ---------------------------------------------------------------------------
from db.db_baseref.SQLAlchemy.public.bas import CBAS

log.info("Chargement de toutes les bases...")

with Session(engine) as session:
    bases = session.scalars(select(CBAS)).all()
    for b in bases:
        log.info(f"  {b.bas_id} | {b.bas_nom} | {b.bas_description}")

log.info(f"{len(bases)} base(s) trouvée(s).")