"""
regenerer_modeles.py  v7
------------------------
Régénère le fichier *_generated.py (SQLAlchemy) pour une base donnée.

Emplacement : projets/BaseRef_Manager_3/Tools/regenerer_modeles.py

Workflow :
    1. Bootstrap + tunnel SSH
    2. Récupère les schémas depuis information_schema
    3. Active ut_sqlacodegen (mot de passe éphémère via sp_sqlacodegen)
    4. Lance sqlacodegen → db/{base}/SQLAlchemy/generated/{base}_generated.py
    5. Désactive ut_sqlacodegen
    6. Post-traitement du fichier généré :
       - Lit pg_catalog pour trouver les colonnes commentées 'encrypted'
       - Remplace LargeBinary par clsEncryptedBytes sur ces colonnes
       - Injecte l'import clsEncryptedBytes en tête du fichier

Vues exclues (--noviews) :
    sqlacodegen génère les vues comme Table() non-mappé (pas de classe ORM)
    car une vue n'a pas de PK définie — requis par SQLAlchemy ORM.
    Les vues sont des outils de requêtage interrogés via SQL direct,
    pas des entités métier à mapper.

Schémas :
    Récupérés depuis information_schema.schemata — source de vérité physique,
    indépendante de tout référentiel applicatif.

Colonnes chiffrées :
    Détectées via le commentaire pg_catalog 'encrypted' sur la colonne.
    Toute colonne BYTEA commentée 'encrypted' est remplacée par clsEncryptedBytes.
    Les colonnes BYTEA sans ce commentaire (images, fichiers...) restent LargeBinary.

Sécurité :
    - ut_sqlacodegen est NOLOGIN par défaut
    - sp_sqlacodegen(TRUE)  : active + mot de passe éphémère (gen_random_bytes)
    - sp_sqlacodegen(FALSE) : désactive + invalide le mot de passe
    - commit() explicite après chaque appel SP (psycopg2 transaction implicite)
    - Le finally garantit désactivation même en cas de plantage
"""

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# Chemins déduits depuis la position du script
# projets/BaseRef_Manager_3/Tools/regenerer_modeles.py
# ---------------------------------------------------------------------------
TOOLS_DIR  = Path(__file__).resolve().parent        # .../Tools/
PROJET_DIR = TOOLS_DIR.parent                       # .../BaseRef_Manager_3/
PYTHON_DIR = PROJET_DIR.parent.parent               # .../Python/

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
PROJET_NOM = "BaseRef_Manager_3"
PROJET_VER = "0.0.1"

from sysclasses.cste_chemins import init_chemins
init_chemins(PROJET_DIR, PROJET_NOM, PROJET_VER)

fichier_ini = PROJET_DIR / "config" / f"{PROJET_NOM}.ini"

from sysclasses.AppBootstrap import AppBootstrap
from sysclasses.clsLOG import clsLOG
from projets.BaseRef_Manager_3.clsINIBaseRef_Manager_3 import clsINIBaseRef_Manager_3

bootstrap = AppBootstrap(fichier_ini, clsINIBaseRef_Manager_3, mode="console")
log = clsLOG()

# ---------------------------------------------------------------------------
# Connexions
# ---------------------------------------------------------------------------
from sysclasses.clsDBAManager import clsDBAManager

dba      = clsDBAManager()
pg_sys   = dba.get_db("POSTGRES")
registry = dba.get_db("__REGISTRY__")

pg_host = "127.0.0.1"

if registry._ssh_tunnel:
    pg_port = registry._ssh_tunnel.local_bind_port
    log.info(f"Tunnel SSH ouvert — port local : {pg_port}")
else:
    pg_port = registry._port or 5432
    log.info(f"Connexion directe — port : {pg_port}")

# ---------------------------------------------------------------------------
# Saisie du nom de la base cible
# ---------------------------------------------------------------------------
NOM_BASE = input("\nNom de la base à régénérer (ex: db_baseref) : ").strip()
if not NOM_BASE:
    log.error("Nom de base vide — abandon.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Chemin destination
# ---------------------------------------------------------------------------
GENERATED_DIR = PYTHON_DIR / "db" / NOM_BASE / "SQLAlchemy" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
outfile = GENERATED_DIR / f"{NOM_BASE}_generated.py"

log.info(f"Base        : {NOM_BASE}")
log.info(f"Destination : {outfile}")

# ---------------------------------------------------------------------------
# Schémas depuis information_schema
# ---------------------------------------------------------------------------
sql_schemas = """
    SELECT schema_name
    FROM   information_schema.schemata
    WHERE  schema_name NOT LIKE 'pg_%%'
    AND    schema_name NOT IN ('information_schema')
    ORDER  BY schema_name
"""
rows    = registry.execute_select(sql_schemas)
schemas = [row["schema_name"] for row in rows]
log.info(f"Schémas trouvés : {', '.join(schemas)}")

# ---------------------------------------------------------------------------
# Colonnes chiffrées depuis pg_catalog
# Détectées via le commentaire 'encrypted' sur la colonne.
# Retourne un set de noms de colonnes commentées 'encrypted' dans la base.
# ---------------------------------------------------------------------------
sql_encrypted = """
    SELECT a.attname AS col_nom
    FROM   pg_attribute    a
    JOIN   pg_class        c ON c.oid      = a.attrelid
    JOIN   pg_namespace    n ON n.oid      = c.relnamespace
    WHERE  a.attnum > 0
    AND    NOT a.attisdropped
    AND    pg_catalog.col_description(a.attrelid, a.attnum) = 'encrypted'
"""
rows_enc       = registry.execute_select(sql_encrypted)
cols_encrypted = {row["col_nom"] for row in rows_enc}
log.info(f"Colonnes chiffrées détectées : {', '.join(sorted(cols_encrypted)) or 'aucune'}")

pwd_ephemere = None

try:
    # -----------------------------------------------------------------------
    # Activation ut_sqlacodegen
    # -----------------------------------------------------------------------
    log.info("Activation de ut_sqlacodegen...")
    result = pg_sys.execute_select("CALL public.sp_sqlacodegen(TRUE, NULL)")
    pg_sys._connection.commit()
    pwd_ephemere = result[0]["p_password"]
    log.debug(f"Mot de passe éphémère reçu : {len(pwd_ephemere)} caractères")

    # -----------------------------------------------------------------------
    # Génération sqlacodegen
    # -----------------------------------------------------------------------
    pg_url      = (
        f"postgresql+psycopg2://ut_sqlacodegen:{quote_plus(pwd_ephemere)}"
        f"@{pg_host}:{pg_port}/{NOM_BASE}"
    )
    schema_args = ["--schemas", ",".join(schemas)]

    cmd = [
        sys.executable, "-m", "sqlacodegen",
        pg_url,
        *schema_args,
        "--noviews",
        "--outfile", str(outfile),
    ]

    if outfile.exists():
        outfile.unlink()
        log.debug(f"{outfile.name} supprimé avant régénération.")

    log.info(f"Génération de {outfile.name}...")
    gen_result = subprocess.run(cmd, capture_output=True, text=True)

    if gen_result.returncode == 0:
        log.info(f"Génération de {outfile.name} — OK")
    else:
        log.error(f"Génération de {outfile.name} — ERREUR")
        log.error(gen_result.stderr.strip())
        sys.exit(1)

finally:
    if pwd_ephemere:
        del pwd_ephemere
    log.info("Désactivation de ut_sqlacodegen...")
    pg_sys.execute_select("CALL public.sp_sqlacodegen(FALSE, NULL)")
    pg_sys._connection.commit()
    log.info("Désactivation de ut_sqlacodegen — OK")

# ---------------------------------------------------------------------------
# Post-traitement — injection de clsEncryptedBytes
# Remplace LargeBinary par clsEncryptedBytes sur les colonnes chiffrées.
# Injecte l'import en tête du fichier si au moins une colonne est concernée.
# ---------------------------------------------------------------------------
if not cols_encrypted:
    log.info("Post-traitement — aucune colonne chiffrée, fichier inchangé.")
else:
    log.info(f"Post-traitement — injection clsEncryptedBytes sur {len(cols_encrypted)} colonne(s)...")

    contenu = outfile.read_text(encoding="utf-8").replace("\r\n", "\n")
    modifie = False

    for col in cols_encrypted:
        pattern      = rf"(^\s*{re.escape(col)}\s*:.*?=\s*mapped_column\()LargeBinary"
        remplacement = r"\1clsEncryptedBytes"
        nouveau, nb  = re.subn(pattern, remplacement, contenu, flags=re.MULTILINE)
        if nb > 0:
            contenu = nouveau
            modifie = True
            log.debug(f"  {col} → clsEncryptedBytes ({nb} occurrence(s))")
        else:
            log.debug(f"  {col} — pattern non trouvé (colonne absente ou déjà traitée)")

    if modifie:
        import_line = "from db.clsEncryptedBytes import clsEncryptedBytes\n"
        # Supprime toute occurrence existante puis réinsère avant class Base
        contenu = contenu.replace(import_line, "")
        contenu = contenu.replace(
            "class Base(DeclarativeBase):",
            import_line + "\nclass Base(DeclarativeBase):",
            1
        )
        outfile.write_text(contenu, encoding="utf-8")
        log.info("Post-traitement — OK")
    else:
        log.warning("Post-traitement — aucune substitution effectuée (vérifier les noms de colonnes).")