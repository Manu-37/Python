-- ================================================================
-- Annulation : retrait ON DELETE CASCADE côté parent fonctionnel
-- Script d'annulation de alter_lco_lre_lel_cascade_parent.sql
-- ================================================================

-- LCO
ALTER TABLE ihm.t_libelle_colonne_lco
    DROP CONSTRAINT fk_lco_col,
    ADD  CONSTRAINT fk_lco_col
        FOREIGN KEY (col_id) REFERENCES ihm.t_colonne_col (col_id);

-- LRE
ALTER TABLE ihm.t_libelle_relation_lre
    DROP CONSTRAINT fk_lre_rel,
    ADD  CONSTRAINT fk_lre_rel
        FOREIGN KEY (rel_id) REFERENCES ihm.t_relation_rel (rel_id);

-- LEL
ALTER TABLE ihm.t_libelle_element_lel
    DROP CONSTRAINT fk_lel_ele,
    ADD  CONSTRAINT fk_lel_ele
        FOREIGN KEY (ele_id) REFERENCES ihm.t_element_ele (ele_id);
