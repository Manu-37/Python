"""
tstat_collecteur.py

Point d'entrée du collecteur Tesla.
Lancé par cron toutes les 5 minutes en production.
Peut être lancé manuellement depuis VSCode ou Jupyter en test.

Rôle :
    1. Initialiser le framework (AppBootstrap mode console)
    2. Charger les véhicules actifs depuis db_tstat_admin
    3. Pour chaque véhicule actif :
        a. Demander à clsFrequenceManager si on doit interroger Tesla
        b. Si oui → lancer clsCollecteur.run()
    4. Logger le résultat et terminer proprement

Déduplication (protection contre chevauchement de cron) :
    Un fichier verrou (.lock) est créé au démarrage et supprimé à la fin.
    Si le verrou existe au démarrage → une instance tourne déjà → on sort immédiatement.
    Le verrou contient le PID courant pour diagnostic.
"""

import sys
import os
from pathlib import Path

# --------------------------------------------------
# Bootstrap du chemin Python
# Doit être fait AVANT tout import projet
# --------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent          # .../projets/tstat_collecteur
_PYTHON_DIR = _SCRIPT_DIR.parent.parent                # .../Python
if str(_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(_PYTHON_DIR))

# --------------------------------------------------
# Imports projet (après ajout au sys.path)
# --------------------------------------------------
from sysclasses.cste_chemins  import init_chemins
from sysclasses.AppBootstrap  import AppBootstrap
from clsINICollecteur         import clsINICollecteur
from clsFrequenceManager      import clsFrequenceManager
from clsCollecteur            import clsCollecteur

# --------------------------------------------------
# Constantes projet
# --------------------------------------------------
PROJET_NOM = "tstat_collecteur"
PROJET_VER = "0.1.0"
INI_FILE   = str(_SCRIPT_DIR / "config" / "tstat_collecteur.ini")


# --------------------------------------------------
# Verrou anti-chevauchement
# --------------------------------------------------

def _acquérir_verrou(chemin_lock: Path) -> bool:
    """
    Crée le fichier verrou si absent.
    Retourne True si le verrou a été acquis, False si déjà présent.
    """
    if chemin_lock.exists():
        try:
            pid_existant = chemin_lock.read_text(encoding="utf-8").strip()
        except OSError:
            pid_existant = "inconnu"
        print(
            f"[tstat_collecteur] Verrou présent (PID={pid_existant}) "
            "— une instance tourne déjà. Sortie.",
            file=sys.stderr
        )
        return False

    chemin_lock.parent.mkdir(parents=True, exist_ok=True)
    chemin_lock.write_text(str(os.getpid()), encoding="utf-8")
    return True


def _liberer_verrou(chemin_lock: Path):
    """Supprime le fichier verrou."""
    try:
        if chemin_lock.exists():
            chemin_lock.unlink()
    except OSError:
        pass


# --------------------------------------------------
# Chargement des véhicules actifs
# --------------------------------------------------

def _charger_vehicules_actifs() -> list:
    """
    Retourne la liste des véhicules actifs depuis db_tstat_data.
    C'est TSTAT_DATA qui est la référence pour le collecteur —
    le veh_id retourné ici est celui utilisé comme FK dans t_snapshot_snp.
    """
    from db.db_tstat_data.public.clsVEH import clsVEH
    from sysclasses.clsDBAManager import clsDBAManager

    engine = clsDBAManager().get_db("TSTAT_DATA")

    sql = (
        f"SELECT * FROM {clsVEH._schema}.{clsVEH._table} "
        f"WHERE {clsVEH.VEH_ISACTIVE} = TRUE "
        f"ORDER BY {clsVEH.VEH_ID}"
    )
    return engine.execute_select(sql)


# --------------------------------------------------
# Traitement d'un véhicule
# --------------------------------------------------

def _traiter_vehicule(veh: dict, params: dict, log) -> None:
    """
    Gère le cycle complet pour un véhicule :
        1. clsFrequenceManager décide si on interroge
        2. clsCollecteur.run() si décision positive
    """
    veh_id  = veh["veh_id"]
    veh_nom = veh.get("veh_displayname") or veh.get("veh_vin", f"id={veh_id}")

    log.info(f"tstat_collecteur | Traitement véhicule : {veh_nom}")

    # --- Décision de fréquence ---
    fm = clsFrequenceManager(params=params, veh_id=veh_id)

    if not fm.doit_interroger():
        log.info(
            f"tstat_collecteur | {veh_nom} — fréquence non atteinte "
            f"(état={fm.etat_courant}) → pas d'appel Tesla."
        )
        return

    # --- Collecte ---
    try:
        collecteur = clsCollecteur(veh_id=veh_id, params=params)
        resultat   = collecteur.run(freq_retry_active=fm.freq_retry_active)

        if resultat["succes"]:
            log.info(
                f"tstat_collecteur | {veh_nom} — "
                f"snapshot enregistré (snp_id={resultat['snp_id']})"
            )
        else:
            log.critical(
                f"tstat_collecteur | {veh_nom} — "
                f"échec collecte : {resultat.get('erreur')}"
            )

    except Exception as e:
        log.critical(
            f"tstat_collecteur | {veh_nom} — exception non gérée : {e}"
        )


# --------------------------------------------------
# Point d'entrée principal
# --------------------------------------------------

def main():
    # --- Chemins ---
    init_chemins(
        app_dir    = _SCRIPT_DIR,
        projet_nom = PROJET_NOM,
        projet_ver = PROJET_VER
    )

    # --- Verrou anti-chevauchement ---
    chemin_lock = _SCRIPT_DIR / "logs" / "tstat_collecteur.lock"
    if not _acquérir_verrou(chemin_lock):
        sys.exit(0)   # Pas une erreur — juste une instance déjà active

    bootstrap = None
    try:
        # --- Bootstrap framework ---
        bootstrap = AppBootstrap(INI_FILE, clsINICollecteur, mode="console")
        log    = bootstrap.oLog
        params = bootstrap.oIni.collecteur_params

        log.info("tstat_collecteur | Démarrage.")

        # --- Véhicules actifs ---
        vehicules = _charger_vehicules_actifs()

        if not vehicules:
            log.warning("tstat_collecteur | Aucun véhicule actif trouvé — fin.")
            return

        log.info(f"tstat_collecteur | {len(vehicules)} véhicule(s) actif(s).")

        # --- Traitement de chaque véhicule ---
        for veh in vehicules:
            _traiter_vehicule(veh, params, log)

        log.info("tstat_collecteur | Traitement terminé.")

    except RuntimeError as e:
        # AppBootstrap lève RuntimeError en mode console sur erreur fatale
        print(f"[ERREUR FATALE] {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        # Filet de sécurité — ne devrait pas arriver
        if bootstrap and hasattr(bootstrap, "oLog"):
            bootstrap.oLog.critical(f"tstat_collecteur | Exception fatale : {e}")
        else:
            print(f"[ERREUR FATALE] {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        _liberer_verrou(chemin_lock)


if __name__ == "__main__":
    main()