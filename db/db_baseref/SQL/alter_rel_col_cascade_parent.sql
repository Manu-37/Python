-- ================================================================
-- Migration : ajout ON DELETE CASCADE côté parent fonctionnel
--             sur REL et COL
--
-- Logique :
--   Si le schéma (sch) est supprimé → ses relations REL disparaissent
--   Si la relation (rel) est supprimée → ses colonnes COL disparaissent
--
-- Combiné aux cascades déjà posées sur LCO, LRE, LEL, cela donne
-- la chaîne complète :
--   SCH → REL → COL → LCO
--              REL → LRE
-- ================================================================

-- REL : sch_id → t_schema_sch
ALTER TABLE ihm.t_relation_rel
    DROP CONSTRAINT fk_rel_sch,
    ADD  CONSTRAINT fk_rel_sch
        FOREIGN KEY (sch_id) REFERENCES ihm.t_schema_sch (sch_id)
        ON DELETE CASCADE;

-- COL : rel_id → t_relation_rel
ALTER TABLE ihm.t_colonne_col
    DROP CONSTRAINT fk_col_rel,
    ADD  CONSTRAINT fk_col_rel
        FOREIGN KEY (rel_id) REFERENCES ihm.t_relation_rel (rel_id)
        ON DELETE CASCADE;
