from sysclasses.clsINICommun import clsINICommun


class clsINICollecteur(clsINICommun):
    """
    Sous-classe INI projet pour tstat_collecteur.
    Ajoute la lecture de la section [COLLECTEUR] au socle clsINICommun.

    Sections attendues dans tstat_collecteur.ini :
        [ENVIRONNEMENT]  — type d'env, path vers security.ini  (clsINICommun)
        [LOG]            — configuration du journal             (clsINICommun)
        [EMAIL_ALERTES]  — profil email pour critical()         (clsINICommun)
        [COLLECTEUR]     — fréquences, plage nocturne, retry    (ici)
    """

    @property
    def collecteur_params(self) -> dict:
        """
        Retourne les paramètres du collecteur avec typage et valeurs par défaut.

        Fréquences (en secondes) :
            freq_charge        : intervalle si véhicule en charge ou en mouvement
            freq_gare_recent   : intervalle si garé depuis moins de seuil_inactif
            freq_gare_inactif  : intervalle si garé depuis plus de seuil_inactif
            freq_nuit          : intervalle pendant la plage nocturne
            seuil_inactif      : durée sans mouvement avant de passer à freq_gare_inactif

        Plage nocturne (heure locale, format HH:MM) :
            nuit_debut         : début de la plage nocturne
            nuit_fin           : fin de la plage nocturne

        Retry :
            seuil_retry_secondes : fréquence minimale pour activer le retry
                                   si freq_courante <= seuil → pas de retry
            retry_tentatives     : nombre de tentatives après le premier échec
            retry_delai          : secondes entre chaque tentative
            retry_max_echecs     : nombre d'échecs consécutifs avant email alerte
        """
        d = self.get_section("COLLECTEUR")

        # --- Fréquences (int, secondes) ---
        d["freq_charge"]        = int(d.get("freq_charge",        300))
        d["freq_gare_recent"]   = int(d.get("freq_gare_recent",  1800))
        d["freq_gare_inactif"]  = int(d.get("freq_gare_inactif", 7200))
        d["freq_nuit"]          = int(d.get("freq_nuit",         7200))
        d["seuil_inactif"]      = int(d.get("seuil_inactif",     3600))

        # --- Plage nocturne (str HH:MM) ---
        d["nuit_debut"] = d.get("nuit_debut", "23:00")
        d["nuit_fin"]   = d.get("nuit_fin",   "06:00")

        # --- Retry ---
        d["seuil_retry_secondes"] = int(d.get("seuil_retry_secondes", 600))
        d["retry_tentatives"]     = int(d.get("retry_tentatives",       3))
        d["retry_delai"]          = int(d.get("retry_delai",           30))
        d["retry_max_echecs"]     = int(d.get("retry_max_echecs",       5))

        return d