-- ================================================================
-- Migration : ajout de lan_ordre sur t_langue_lan
-- Ordre d'affichage des langues dans les composants multilingues.
-- DEFAULT 0 — toutes les lignes existantes prennent 0.
-- ================================================================

ALTER TABLE ihm.t_langue_lan
    ADD COLUMN lan_ordre INTEGER NOT NULL DEFAULT 0;
