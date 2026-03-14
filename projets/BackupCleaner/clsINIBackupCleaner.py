from sysclasses.clsINICommun import clsINICommun


class clsINIBackupCleaner(clsINICommun):
    """
    Classe INI du projet BackupCleaner.
    Étend clsINICommun avec les paramètres spécifiques à la purge.
    """

    @property
    def purge_params(self) -> dict:
        """
        Récupère la section [PURGE] et convertit les types.

        Clés attendues :
            backup_folder   : chemin OneDrive des sauvegardes (str)
            retention_jours : nombre de jours de rétention    (int, défaut : 30)
            email_profil    : profil email pour le résumé     (str, défaut : ALERTES)
        """
        d = self.get_section("PURGE")
        if 'retention_jours' in d:
            d['retention_jours'] = int(d['retention_jours'])
        else:
            d['retention_jours'] = 30
        if 'email_profil' not in d:
            d['email_profil'] = 'ALERTES'
        else:
            d['email_profil'] = d['email_profil'].upper()
        return d
