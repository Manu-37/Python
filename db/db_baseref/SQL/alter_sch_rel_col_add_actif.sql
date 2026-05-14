-- ================================================================
-- Migration : ajout _actif sur t_schema_sch, t_relation_rel,
--             t_colonne_col
-- Flag de désactivation logique utilisé par l'explorateur lors
-- d'une disparition détectée — cascade silencieuse sur les
-- descendants sans suppression physique.
-- DEFAULT TRUE — toutes les lignes existantes restent actives.
-- ================================================================

ALTER TABLE ihm.t_schema_sch
    ADD COLUMN sch_actif BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE ihm.t_relation_rel
    ADD COLUMN rel_actif BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE ihm.t_colonne_col
    ADD COLUMN col_actif BOOLEAN NOT NULL DEFAULT TRUE;
