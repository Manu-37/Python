import configparser
import os


class clsINI:
    """
    Gestionnaire technique universel pour fichiers .ini.

    INSTANCIATION DIRECTE INTERDITE.
    Hériter de clsINICommun qui elle-même hérite de cette classe.
    """

    def __new__(cls, *args, **kwargs):
        if cls is clsINI:
            raise TypeError(
                "clsINI ne peut pas être instanciée directement.\n"
                "Utilisez clsINICommun ou une sous-classe projet."
            )
        return super().__new__(cls)

    def __init__(self, filename: str):
        self._filename = filename
        self._config   = configparser.ConfigParser(interpolation=None)
        if not os.path.exists(self._filename):
            raise FileNotFoundError(f"Fichier introuvable : {self._filename}")
        self._config.read(self._filename, encoding='utf-8')

    def get_str(self, section: str, key: str, default: str = "") -> str:
        return self._config.get(section, key, fallback=default)

    def get_section(self, section: str) -> dict:
        if self._config.has_section(section):
            return dict(self._config.items(section))
        return {}