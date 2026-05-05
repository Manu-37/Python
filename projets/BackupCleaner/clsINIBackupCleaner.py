from sysclasses.clsINICommun import clsINICommun


class clsINIBackupCleaner(clsINICommun):
    """
    Classe INI du projet BackupCleaner.
    Étend clsINICommun avec les paramètres spécifiques à la purge.
    """

    @property
    def purge_params(self) -> dict:
        """Récupère la section [PURGE] — backup_folder et email_profil."""
        d = self.get_section("PURGE")
        if 'email_profil' not in d:
            d['email_profil'] = 'ALERTES'
        else:
            d['email_profil'] = d['email_profil'].upper()
        return d
