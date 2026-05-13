-- ================================================================
-- Migration : ajout de lco_label_court sur t_libelle_colonne_lco
-- Libellé court (≤ 15 car.) utilisé pour les en-têtes de colonnes
-- resserrées ou tout affichage espace contraint.
-- Nullable — non obligatoire.
-- ================================================================

ALTER TABLE ihm.t_libelle_colonne_lco
    ADD COLUMN lco_label_court VARCHAR(15);
