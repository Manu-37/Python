from .clsDB_ABS import clsDB_ABS


class clsStat_ABS(clsDB_ABS):
    """
    Socle des classes d'analyse statistique et de requêtage agrégé.
    Hérite de clsDB_ABS : ogLog, ogEngine, _build_where, _date_trunc.

    Contrairement aux entités (clsEntity_ABS), ces classes ne représentent
    pas une ligne de table — elles exécutent des requêtes multi-lignes
    sur des tables ou des vues matérialisées.
    Requêtes uniquement en lecture — pas de CRUD, car pas de PK, pas de validation de valeurs.

    """
    pass