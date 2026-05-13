-- ================================================================
-- Annulation : suppression de lan_ordre sur t_langue_lan
-- Script d'annulation de alter_lan_add_ordre.sql
-- ================================================================

ALTER TABLE ihm.t_langue_lan
    DROP COLUMN IF EXISTS lan_ordre;
