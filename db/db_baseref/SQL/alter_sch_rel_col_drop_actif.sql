-- ================================================================
-- Rollback : suppression _actif sur t_colonne_col, t_relation_rel,
--            t_schema_sch (ordre inverse des dépendances)
-- ================================================================

ALTER TABLE ihm.t_colonne_col  DROP COLUMN IF EXISTS col_actif;
ALTER TABLE ihm.t_relation_rel DROP COLUMN IF EXISTS rel_actif;
ALTER TABLE ihm.t_schema_sch   DROP COLUMN IF EXISTS sch_actif;
