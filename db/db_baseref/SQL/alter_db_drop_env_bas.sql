-- ================================================================
-- Rollback : suppression env_id et bas_id de t_db_db
-- ================================================================

ALTER TABLE ihm.t_db_db
    DROP CONSTRAINT IF EXISTS fk_db_env,
    DROP CONSTRAINT IF EXISTS fk_db_bas,
    DROP COLUMN    IF EXISTS  env_id,
    DROP COLUMN    IF EXISTS  bas_id;
