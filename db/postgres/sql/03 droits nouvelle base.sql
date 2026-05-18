-- =============================================================================
-- 03_droits_nouvelle_base.sql
-- =============================================================================
-- À exécuter sur CHAQUE base opérationnelle à exposer à sqlacodegen.
-- Sera intégré à terme dans la procédure de création de base.
--
-- Prérequis :
--   - 01_creation_roles.sql exécuté
--   - Se connecter à la base cible dans pgAdmin avant d'exécuter
--   - Être connecté en superuser
--
-- Personnalisation :
--   - Remplacer db_baseref par le nom réel de la base (ligne GRANT CONNECT)
--   - Ajouter un bloc GRANT USAGE par schéma supplémentaire
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Droit de connexion sur la base
-- -----------------------------------------------------------------------------
GRANT CONNECT ON DATABASE db_tstat_data TO r_sqlacodegen;


-- -----------------------------------------------------------------------------
-- Lecture information_schema
-- sqlacodegen lit information_schema pour l'introspection des tables,
-- colonnes, contraintes et relations.
-- pg_catalog est accessible par défaut — pas de GRANT nécessaire.
-- -----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA information_schema TO r_sqlacodegen;
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO r_sqlacodegen;


-- -----------------------------------------------------------------------------
-- Droits sur les schémas opérationnels
-- USAGE uniquement — pas de SELECT sur les tables métier.
-- sqlacodegen n'a besoin que de lire les métadonnées, jamais les données.
--
-- Dupliquer le bloc GRANT USAGE pour chaque schéma de la base.
-- -----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO r_sqlacodegen;
-- GRANT USAGE ON SCHEMA cron TO r_sqlacodegen;
-- GRANT USAGE ON SCHEMA mon_schema TO r_sqlacodegen;