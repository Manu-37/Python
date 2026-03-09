import configparser
import os

class clsINI:
    """
    Gestionnaire technique universel pour fichiers .ini.
    """
    def __init__(self, filename: str):
        self._filename = filename
        self._config = configparser.ConfigParser()
        if not os.path.exists(self._filename):
            raise FileNotFoundError(f"Fichier introuvable : {self._filename}")
        self._config.read(self._filename, encoding='utf-8')

    def get_str(self, section: str, key: str, default: str = "") -> str:
        return self._config.get(section, key, fallback=default)

    def get_section(self, section: str) -> dict:
        if self._config.has_section(section):
            return dict(self._config.items(section))
        return {}