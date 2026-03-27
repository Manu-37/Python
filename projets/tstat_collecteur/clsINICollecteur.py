from sysclasses.clsINICommun import clsINICommun


class clsINICollecteur(clsINICommun):
    """
    Sous-classe INI projet pour tstat_collecteur.
    Ajoute la lecture de la section [COLLECTEUR] au socle clsINICommun.

    Sections attendues dans tstat_collecteur.ini :
        [ENVIRONNEMENT]  — type d'env, path vers security.ini  (clsINICommun)
        [LOG]            — configuration du journal             (clsINICommun)
        [EMAIL_ALERTES]  — profil email pour critical()         (clsINICommun)
        [COLLECTEUR]     — fréquences et retry                  (ici)

    Clés INI section [COLLECTEUR] :
        freq_charge          = 300    # secondes entre deux collectes en charge
        freq_conduite        = 300    # secondes entre deux collectes hors charge
        seuil_retry_secondes = 600    # freq minimale pour activer le retry
        retry_tentatives     = 3
        retry_delai          = 30
        retry_max_echecs     = 5

    Clés OBSOLETES conservées pour retour arrière éventuel
    (lues mais ignorées par clsFrequenceManager) :
        freq_gare_recent     = 1800
        freq_gare_inactif    = 7200
        freq_nuit            = 7200
        seuil_inactif        = 3600
        nuit_debut           = 23:00
        nuit_fin             = 06:00
    """

    @property
    def collecteur_params(self) -> dict:
        """
        Retourne les paramètres du collecteur avec typage et valeurs par défaut.

        Fréquences actives :
            freq_charge   : intervalle si véhicule en charge
                            Appliqué même la nuit — on ne rate pas Complete/Stopped.
            freq_conduite : intervalle pour tout le reste (conduite, garé, nuit)
                            Le véhicule s'endort de lui-même si inactif.

        Retry :
            seuil_retry_secondes : fréquence minimale pour activer le retry
                                   si freq_courante <= seuil → pas de retry
            retry_tentatives     : nombre de tentatives après le premier échec
            retry_delai          : secondes entre chaque tentative
            retry_max_echecs     : nombre d'échecs consécutifs avant email alerte
        """
        d = self.get_section("COLLECTEUR")

        # --- Fréquences actives ---
        d["freq_charge"]   = int(d.get("freq_charge",   300))
        d["freq_conduite"] = int(d.get("freq_conduite", 300))

        # --- OBSOLETE — lus pour ne pas planter si présents dans le .ini ---
        # clsFrequenceManager ne les utilise plus mais ils peuvent rester dans
        # le fichier ini sans provoquer d'erreur.
        d["freq_gare_recent"]  = int(d.get("freq_gare_recent",  1800))
        d["freq_gare_inactif"] = int(d.get("freq_gare_inactif", 7200))
        d["freq_nuit"]         = int(d.get("freq_nuit",         7200))
        d["seuil_inactif"]     = int(d.get("seuil_inactif",     3600))
        d["nuit_debut"]        = d.get("nuit_debut", "23:00")
        d["nuit_fin"]          = d.get("nuit_fin",   "06:00")

        # --- Retry ---
        d["seuil_retry_secondes"] = int(d.get("seuil_retry_secondes", 600))
        d["retry_tentatives"]     = int(d.get("retry_tentatives",       3))
        d["retry_delai"]          = int(d.get("retry_delai",           30))
        d["retry_max_echecs"]     = int(d.get("retry_max_echecs",       5))

        return d