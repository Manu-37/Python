-- ================================================================
-- Correction contrainte unique — ihm.t_schema_sch
-- La contrainte uq_sch portait sur sch_nom seul alors qu'un même
-- nom de schéma peut exister dans plusieurs bases distinctes.
-- La contrainte correcte est composite : (db_id, sch_nom).
-- ================================================================

ALTER TABLE ihm.t_schema_sch
    DROP CONSTRAINT IF EXISTS uq_sch;

ALTER TABLE ihm.t_schema_sch
    ADD CONSTRAINT uq_sch UNIQUE (db_id, sch_nom);
