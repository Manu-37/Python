-- Migration : index unique (rel_id, col_nom) sur t_colonne_col
-- Garantit l'absence de doublons nom de colonne dans une même relation.
-- Utiliser IF NOT EXISTS pour rejouer sans erreur.
-- ATTENTION : si des doublons existent déjà, nettoyer avant d'appliquer :
--   DELETE FROM ihm.t_colonne_col WHERE col_id NOT IN (
--       SELECT MIN(col_id) FROM ihm.t_colonne_col GROUP BY rel_id, col_nom
--   );

CREATE UNIQUE INDEX IF NOT EXISTS uq_col_rel_nom
    ON ihm.t_colonne_col (rel_id, col_nom);
