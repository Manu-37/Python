"""
BackupCleaner.py
Purge des fichiers de sauvegarde OneDrive selon une politique GFS.
Exécuté quotidiennement par le Planificateur de tâches Windows.
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from collections import defaultdict

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
PROJET_VER = "0.1.0"
INI_FILE   = _PROJET_DIR / "config" / "BackupCleaner.ini"

_PATTERN_DATE = re.compile(r'_(\d{8})_\d{6}\.dump$')


def _date_depuis_nom(fichier: Path) -> date | None:
    m = _PATTERN_DATE.search(fichier.name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), '%Y%m%d').date()
    except ValueError:
        return None


def _dernier_jour_du_mois(d: date) -> date:
    if d.month == 12:
        return date(d.year, 12, 31)
    return date(d.year, d.month + 1, 1) - timedelta(days=1)


def _fichiers_a_conserver(fichiers: list, aujourd_hui: date) -> set:
    """
    Politique GFS :
      < 7 jours    : tout garder
      7–30 jours   : dernier dump de chaque jour
      31–365 jours : dernier dump du dimanche de chaque semaine ISO
                     + dernier dump du dernier jour de chaque mois
                     (fallback : dernier jour disponible si le jour pivot est absent)
      > 365 jours  : dernier dump du 31/12 de chaque année
                     (fallback : dernier jour disponible de l'année)
    Les fichiers au nom non parsable sont toujours conservés.
    """
    conserver = set()
    par_date: dict[date, list] = defaultdict(list)

    for f in fichiers:
        d = _date_depuis_nom(f)
        if d is None:
            conserver.add(f)
        else:
            par_date[d].append(f)

    # Fenêtre 1 : < 7 jours — tout garder
    for d, fics in par_date.items():
        if (aujourd_hui - d).days < 7:
            conserver.update(fics)

    # Fenêtre 2 : 7–30 jours — dernier dump de chaque journée
    for d, fics in par_date.items():
        delta = (aujourd_hui - d).days
        if 7 <= delta < 31:
            conserver.add(sorted(fics)[-1])

    # Fenêtres 3 et 4 — regroupements par semaine / mois / année
    dates_f3 = [d for d in par_date if 31 <= (aujourd_hui - d).days <= 365]
    dates_f4 = [d for d in par_date if (aujourd_hui - d).days > 365]

    # Fenêtre 3a : 1/semaine — préférer dimanche, sinon dernier jour dispo
    par_semaine: dict[tuple, list] = defaultdict(list)
    for d in dates_f3:
        iso = d.isocalendar()
        par_semaine[(iso.year, iso.week)].append(d)

    for dates_sem in par_semaine.values():
        dates_sem = sorted(dates_sem)
        dimanches = [d for d in dates_sem if d.weekday() == 6]
        pivot = dimanches[-1] if dimanches else dates_sem[-1]
        conserver.add(sorted(par_date[pivot])[-1])

    # Fenêtre 3b : 1/mois — préférer dernier jour du mois, sinon dernier jour dispo
    par_mois: dict[tuple, list] = defaultdict(list)
    for d in dates_f3:
        par_mois[(d.year, d.month)].append(d)

    for dates_mois in par_mois.values():
        dates_mois = sorted(dates_mois)
        fin_mois = _dernier_jour_du_mois(dates_mois[0])
        fins = [d for d in dates_mois if d == fin_mois]
        pivot = fins[-1] if fins else dates_mois[-1]
        conserver.add(sorted(par_date[pivot])[-1])

    # Fenêtre 4 : > 365 jours — préférer 31/12, sinon dernier jour dispo de l'année
    par_annee: dict[int, list] = defaultdict(list)
    for d in dates_f4:
        par_annee[d.year].append(d)

    for dates_an in par_annee.values():
        dates_an = sorted(dates_an)
        dec31 = [d for d in dates_an if d.month == 12 and d.day == 31]
        pivot = dec31[-1] if dec31 else dates_an[-1]
        conserver.add(sorted(par_date[pivot])[-1])

    return conserver


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

    def _gestion_exception_globale(exc_type, exc_value, exc_traceback):
        oLog.critical(f"Exception non gérée : {exc_type.__name__} — {exc_value}")

    sys.excepthook = _gestion_exception_globale

    # --------------------------------------------------
    # 2. Lecture des paramètres
    # --------------------------------------------------
    try:
        purge         = bootstrap.oIni.purge_params
        backup_folder = Path(purge['backup_folder'])
        email_profil  = purge['email_profil']
    except Exception as e:
        oLog.critical(f"BackupCleaner | Paramètres [PURGE] invalides — {e}")
        return

    oLog.info(f"BackupCleaner | Dossier : {backup_folder} | Politique : GFS")

    # --------------------------------------------------
    # 3. Vérification du dossier
    # --------------------------------------------------
    if not backup_folder.is_dir():
        oLog.critical(f"BackupCleaner | Dossier introuvable : {backup_folder}")
        return

    # --------------------------------------------------
    # 4. Purge GFS par sous-dossier (une base = un sous-dossier)
    # --------------------------------------------------
    aujourd_hui    = datetime.now().date()
    supprimes      = []
    erreurs        = []
    octets_liberes = 0

    for sous_dossier in sorted(backup_folder.iterdir()):
        if not sous_dossier.is_dir():
            continue

        fichiers    = [f for f in sous_dossier.iterdir() if f.is_file()]
        a_conserver = _fichiers_a_conserver(fichiers, aujourd_hui)

        for fichier in fichiers:
            if fichier in a_conserver:
                continue
            try:
                taille = fichier.stat().st_size
                fichier.unlink()
                supprimes.append(fichier.name)
                octets_liberes += taille
                oLog.info(f"BackupCleaner | Supprimé : {fichier.name}")
            except Exception as e:
                msg = f"{fichier.name} — {e}"
                erreurs.append(msg)
                oLog.error(f"BackupCleaner | Erreur suppression : {msg}")

    # --------------------------------------------------
    # 5. Résumé log
    # --------------------------------------------------
    oLog.info(
        f"BackupCleaner | Résumé — {len(supprimes)} fichier(s) supprimé(s), "
        f"{octets_liberes / 1024 / 1024:.2f} Mo libérés, {len(erreurs)} erreur(s)"
    )

    # --------------------------------------------------
    # 6. Email résumé quotidien
    # --------------------------------------------------
    _envoyer_resume(oEmail, email_profil, oLog,
                    supprimes, erreurs, octets_liberes, backup_folder)


def _envoyer_resume(oEmail, profil: str, oLog,
                    supprimes: list, erreurs: list,
                    octets_liberes: int, backup_folder: Path):
    """Construit et envoie le résumé quotidien par email."""

    mo_liberes = octets_liberes / (1024 * 1024)
    today      = datetime.now().strftime('%d/%m/%Y')
    statut     = "OK" if not erreurs else "AVEC ERREURS"

    lignes = [
        f"BackupCleaner — Résumé du {today}",
        f"Statut          : {statut}",
        f"Dossier         : {backup_folder}",
        f"Politique       : GFS — <7j tout / <30j 1/jour / <1an dim.+fin-mois / >1an 31/12",
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
