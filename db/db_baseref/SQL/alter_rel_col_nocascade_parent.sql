-- ================================================================
-- Rollback : suppression ON DELETE CASCADE sur REL et COL
--            (restauration en RESTRICT / NO ACTION par défaut)
-- ================================================================

-- COL : rel_id → t_relation_rel
ALTER TABLE ihm.t_colonne_col
    DROP CONSTRAINT fk_col_rel,
    ADD  CONSTRAINT fk_col_rel
        FOREIGN KEY (rel_id) REFERENCES ihm.t_relation_rel (rel_id);

-- REL : sch_id → t_schema_sch
ALTER TABLE ihm.t_relation_rel
    DROP CONSTRAINT fk_rel_sch,
    ADD  CONSTRAINT fk_rel_sch
        FOREIGN KEY (sch_id) REFERENCES ihm.t_schema_sch (sch_id);
