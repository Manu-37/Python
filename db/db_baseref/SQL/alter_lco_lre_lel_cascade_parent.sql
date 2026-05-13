-- ================================================================
-- Migration : ajout ON DELETE CASCADE côté parent fonctionnel
--             sur LCO, LRE, LEL
--
-- Logique :
--   Si la colonne (col) est supprimée → ses libellés LCO disparaissent
--   Si la relation (rel) est supprimée → ses libellés LRE disparaissent
--   Si l'élément (ele) est supprimé   → ses libellés LEL disparaissent
--
-- La FK côté langue (lan_id) n'est PAS cascadée —
-- supprimer une langue ne supprime pas les libellés des autres entités.
-- ================================================================

-- LCO : col_id → t_colonne_col
ALTER TABLE ihm.t_libelle_colonne_lco
    DROP CONSTRAINT fk_lco_col,
    ADD  CONSTRAINT fk_lco_col
        FOREIGN KEY (col_id) REFERENCES ihm.t_colonne_col (col_id)
        ON DELETE CASCADE;

-- LRE : rel_id → t_relation_rel
ALTER TABLE ihm.t_libelle_relation_lre
    DROP CONSTRAINT fk_lre_rel,
    ADD  CONSTRAINT fk_lre_rel
        FOREIGN KEY (rel_id) REFERENCES ihm.t_relation_rel (rel_id)
        ON DELETE CASCADE;

-- LEL : ele_id → t_element_ele
ALTER TABLE ihm.t_libelle_element_lel
    DROP CONSTRAINT fk_lel_ele,
    ADD  CONSTRAINT fk_lel_ele
        FOREIGN KEY (ele_id) REFERENCES ihm.t_element_ele (ele_id)
        ON DELETE CASCADE;
