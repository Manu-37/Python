from sysclasses.clsINI import clsINI
from pathlib import Path

class clsINICommun(clsINI):
    """Fournit les propriétés obligatoires par blocs, sans mapping manuel par clé."""

    def __init__(self, filename):
        super().__init__(filename)

    @property
    def project_params(self) -> dict:
        """Récupère tout PROJECT et force les majuscules sur le nom."""
        d = self.get_section("PROJECT")
        if 'name' in d: d['name'] = d['name'].upper()
        return d

    @property
    def env_params(self) -> dict:
        """Récupère tout ENVIRONNEMENT et gère le booléen."""
        d = self.get_section("ENVIRONNEMENT")
        # On gère juste la conversion technique, le reste passe tel quel
        if 'ssh_enabled' in d:
            d['ssh_enabled'] = d['ssh_enabled'].upper() == 'TRUE'
        return d

    @property
    def log_params(self) -> dict:
        """Récupère tout LOG et résout le chemin du dossier."""
        d = self.get_section("LOG")
        # Traitement spécifique pour le chemin
        if 'folder' in d:
            p = Path(d['folder'])
            if not p.is_absolute():
                d['folder'] = str((Path(self._filename).parent / p).resolve())
        # Conversion automatique des types numériques si présents
        for key in ['level', 'max_bytes', 'backup_count']:
            if key in d: d[key] = int(d[key])
        return d

    @property
    def db_baseref_ssh_params(self) -> dict:
        """Récupère tout DE_BASEREF.SSH_GATEWAY sans connaître les clés à l'avance."""
        d = self.get_section("SSH_GATEWAY")
        if 'port' in d: d['port'] = int(d['port'])
        return d

    @property
    def db_baseref_params(self) -> dict:
        """Récupère tout DB_BASEREF.DB_BASEREF."""
        d = self.get_section("DB_BASEREF")
        if 'port' in d: d['port'] = int(d['port'])
        return d
    
    @property
    def db_baseref_security(self) -> dict:
        """Récupère tout DB_BASEREF.SECURITY."""
        d = self.get_section("SECURITY")
        return d