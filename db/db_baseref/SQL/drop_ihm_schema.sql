-- ================================================================
-- ROLLBACK — Suppression du schéma IHM
-- Base cible : db_baseref
--
-- CASCADE supprime en cascade :
--   tables    : t_langue_lan, t_application_app, t_type_element_tel,
--               t_db_db, t_type_relation_tre, t_type_affichage_taf,
--               t_app_lan_nal, t_schema_sch, t_element_ele,
--               t_relation_rel, t_libelle_relation_lre,
--               t_libelle_element_lel, t_colonne_col, t_libelle_colonne_lco
--   fonctions : fn_audit_ihm()
--   triggers  : tous les trg_audit_*
--   séquences : toutes les séquences BIGSERIAL
--
-- ATTENTION : opération irréversible — toutes les données sont perdues
-- ================================================================

DROP SCHEMA IF EXISTS ihm CASCADE;
