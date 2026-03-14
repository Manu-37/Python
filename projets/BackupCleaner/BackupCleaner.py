"""
BackupCleaner.py
Purge des fichiers de sauvegarde OneDrive plus anciens que N jours.
Exécuté quotidiennement par le Planificateur de tâches Windows.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# --------------------------------------------------
# Résolution des chemins — doit être fait AVANT tout import sysclasses
# --------------------------------------------------
_PROJET_DIR = Path(__file__).resolve().parent
_PYTHON_DIR = _PROJET_DIR.parent.parent
sys.path.insert(0, str(_PYTHON_DIR))

from sysclasses.cste_chemins    import init_chemins
from sysclasses.AppBootstrap    import AppBootstrap
from sysclasses.clsLOG          import clsLOG
from sysclasses.clsEmailManager import clsEmailManager
from projets.BackupCleaner.clsINIBackupCleaner import clsINIBackupCleaner

# --------------------------------------------------
# Constantes projet
# --------------------------------------------------
PROJET_NOM = "BackupCleaner"
PROJET_VER = "0.0.1"
INI_FILE   = _PROJET_DIR / "config" / "BackupCleaner.ini"


def main():

    # --------------------------------------------------
    # 1. Init chemins + bootstrap complet
    # --------------------------------------------------
    init_chemins(_PROJET_DIR, PROJET_NOM, PROJET_VER)

    try:
        bootstrap = AppBootstrap(INI_FILE, clsINIBackupCleaner, mode='console')
    except RuntimeError:
        return

    oLog   = clsLOG()
    oEmail = clsEmailManager()

    # --------------------------------------------------
    # Intercepteur global — toute exception non gérée est loggée en critical
    # ce qui en PROD déclenche automatiquement le mail d'alerte
    # --------------------------------------------------
    def _gestion_exception_globale(exc_type, exc_value, exc_traceback):
        oLog.critical(f"Exception non gérée : {exc_type.__name__} — {exc_value}")

    sys.excepthook = _gestion_exception_globale

    # --------------------------------------------------
    # 2. Lecture des paramètres de purge
    # --------------------------------------------------
    try:
        purge           = bootstrap.oIni.purge_params
        backup_folder   = Path(purge['backup_folder'])
        retention_jours = purge['retention_jours']
        email_profil    = purge['email_profil']
    except Exception as e:
        oLog.critical(f"BackupCleaner | Paramètres [PURGE] invalides — {e}")
        return

    oLog.info(f"BackupCleaner | Dossier : {backup_folder} | Rétention : {retention_jours} jours")

    # --------------------------------------------------
    # 3. Vérification du dossier
    # --------------------------------------------------
    if not backup_folder.is_dir():
        oLog.critical(f"BackupCleaner | Dossier introuvable : {backup_folder}")
        return

    # --------------------------------------------------
    # 4. Purge
    # --------------------------------------------------
    date_limite    = datetime.now() - timedelta(days=retention_jours)
    supprimes      = []
    erreurs        = []
    octets_liberes = 0

    for fichier in backup_folder.rglob('*'):
        if not fichier.is_file():
            continue
        try:
            mtime = datetime.fromtimestamp(fichier.stat().st_mtime)
            if mtime < date_limite:
                taille = fichier.stat().st_size
                fichier.unlink()
                supprimes.append(fichier.name)
                octets_liberes += taille
                oLog.info(f"BackupCleaner | Supprimé : {fichier.name} ({mtime:%Y-%m-%d})")
        except Exception as e:
            msg_erreur = f"{fichier.name} — {e}"
            erreurs.append(msg_erreur)
            oLog.error(f"BackupCleaner | Erreur suppression : {msg_erreur}")

    # --------------------------------------------------
    # 5. Résumé log
    # --------------------------------------------------
    mo_liberes = octets_liberes / (1024 * 1024)
    oLog.info(
        f"BackupCleaner | Résumé — {len(supprimes)} fichier(s) supprimé(s), "
        f"{mo_liberes:.2f} Mo libérés, {len(erreurs)} erreur(s)"
    )

    # --------------------------------------------------
    # 6. Email résumé quotidien
    # --------------------------------------------------
    _envoyer_resume(oEmail, email_profil, oLog,
                    supprimes, erreurs, octets_liberes,
                    backup_folder, retention_jours)


def _envoyer_resume(oEmail, profil: str, oLog,
                    supprimes: list, erreurs: list,
                    octets_liberes: int, backup_folder: Path,
                    retention_jours: int):
    """Construit et envoie le résumé quotidien par email."""

    mo_liberes = octets_liberes / (1024 * 1024)
    today      = datetime.now().strftime('%d/%m/%Y')
    statut     = "OK" if not erreurs else "AVEC ERREURS"

    lignes = [
        f"BackupCleaner — Résumé du {today}",
        f"Statut          : {statut}",
        f"Dossier         : {backup_folder}",
        f"Rétention       : {retention_jours} jours",
        "",
        f"Fichiers supprimés : {len(supprimes)}",
        f"Espace libéré      : {mo_liberes:.2f} Mo",
    ]

    if supprimes:
        lignes += ["", "Fichiers supprimés :"]
        lignes += [f"  - {f}" for f in supprimes]

    if erreurs:
        lignes += ["", "Erreurs :"]
        lignes += [f"  - {e}" for e in erreurs]

    corps = "\n".join(lignes)
    sujet = f"[BackupCleaner] Résumé {today} — {len(supprimes)} fichier(s) supprimé(s)"

    ok = oEmail.envoyer(profil=profil, sujet=sujet, corps=corps)
    if not ok:
        oLog.warning("BackupCleaner | Échec envoi email résumé.")


if __name__ == "__main__":
    main()