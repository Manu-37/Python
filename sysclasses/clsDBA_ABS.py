from abc import ABC, abstractmethod

class clsDBA_ABS(ABC):
    def __init__(self, log):
        """Initialisation de base partagée par toutes les bases de données relationnelles."""
        self._log = log
        self._connection = None
        self._ssh_tunnel = None

    @abstractmethod
    def connect(self, host, port, dbname, user, pwd): pass

    @abstractmethod
    def disconnect(self): pass

    @abstractmethod
    def execute_select(self, command: str, params: tuple = None, as_dict: bool = True): pass

    @abstractmethod
    def execute_non_query(self, command: str, params: tuple = None): pass

    @abstractmethod
    def _get_cursor(self): pass