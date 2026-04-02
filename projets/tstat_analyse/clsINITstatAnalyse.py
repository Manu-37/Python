from sysclasses.clsINICommun import clsINICommun


class clsINITstatAnalyse(clsINICommun):
    """
    Classe INI du projet tstat_analyse.
    Hérite de clsINICommun sans extension pour l'instant —
    toutes les sections nécessaires (ENVIRONNEMENT, LOG, EMAIL_*)
    sont couvertes par clsINICommun.

    Si des sections spécifiques à tstat_analyse sont ajoutées au .ini
    dans le futur (ex : [DASHBOARD], [STREAMLIT]), leurs propriétés
    seront déclarées ici.
    """
    pass