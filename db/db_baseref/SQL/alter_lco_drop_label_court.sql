-- ================================================================
-- Annulation : suppression de lco_label_court sur t_libelle_colonne_lco
-- Script d'annulation de alter_lco_add_label_court.sql
-- ================================================================

ALTER TABLE ihm.t_libelle_colonne_lco
    DROP COLUMN IF EXISTS lco_label_court;
