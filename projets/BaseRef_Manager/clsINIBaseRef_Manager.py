from sysclasses.clsINICommun import clsINICommun


class clsINIBaseRef_Manager(clsINICommun):
    """
    Classe INI du projet BaseRef_Manager.
    Hérite de clsINICommun sans extension pour l'instant —
    toutes les sections nécessaires (DB_BASEREF, SSH_GATEWAY, SECURITY,
    ENVIRONNEMENT, LOG, EMAIL_*) sont déjà couvertes par clsINICommun.

    Si des sections spécifiques à BaseRef_Manager sont ajoutées au .ini
    dans le futur, leurs propriétés seront déclarées ici.
    """
    pass
