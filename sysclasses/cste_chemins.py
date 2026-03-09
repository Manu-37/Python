from pathlib import Path

# Variables PRIVÉES au module.
# Le préfixe _ signifie : "usage interne, ne pas importer directement".
_APP_DIR: Path    = Path('')
_PYTHON_DIR: Path = Path('')


def init_chemins(app_dir: Path) -> None:
    """
    Appelée UNE SEULE FOIS au démarrage, depuis le point d'entrée du projet
    (ex: BaseRef_Manager.py).
    Fixe les deux chemins racines pour toute l'application.
    """
    global _APP_DIR, _PYTHON_DIR
    _APP_DIR    = app_dir
    _PYTHON_DIR = app_dir.parent.parent.resolve()  # remonte deux niveaux jusqu'à DEV/Python


def get_app_dir() -> Path:
    """Retourne le dossier racine du projet en cours (ex: .../Python/projets/BaseRef_Manager)."""
    return _APP_DIR


def get_python_dir() -> Path:
    """Retourne le dossier Python parent (ex: .../Python) — contient logs, projets, sysclasses, db."""
    return _PYTHON_DIR
