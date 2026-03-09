from SysClasses.clsINICommun import clsINICommun

class clsINITSTAT(clsINICommun):
    """Spécificités métiers pour Tesla TSTAT."""
    
    @property
    def tesla_polling_sec(self) -> int:
        return int(self.get_str("TESLA", "polling", default="600"))

    def get_db_params(self) -> dict:
        # Logique de sélection de la base selon l'environnement (DEV=MSSQL, PROD=SQLITE)
        section = "DB_MAIN" if self.env_type == "DEV" else "DB_SQLITE"
        return self.get_section(section)