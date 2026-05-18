-- =============================================================================
-- 01_creation_roles.sql
-- =============================================================================
-- À exécuter UNE SEULE FOIS sur la base système "postgres" en tant que superuser.
--
-- Crée :
--   - pgcrypto                : extension nécessaire pour gen_random_bytes
--   - r_sqlacodegen           : rôle porteur des droits de lecture schéma
--   - ut_sqlacodegen          : compte applicatif NOLOGIN par défaut
--
-- Prérequis : être connecté à la base postgres en superuser
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Extension pgcrypto
--    Nécessaire pour gen_random_bytes dans sp_sqlacodegen.
--    Sans effet si déjà installée.
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- -----------------------------------------------------------------------------
-- 2. Rôle porteur r_sqlacodegen
--    Droits minimaux : lecture des métadonnées uniquement, jamais des données.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'r_sqlacodegen') THEN
        CREATE ROLE r_sqlacodegen
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOLOGIN;
        RAISE NOTICE 'Rôle r_sqlacodegen créé.';
    ELSE
        RAISE NOTICE 'Rôle r_sqlacodegen existe déjà — ignoré.';
    END IF;
END;
$$;


-- -----------------------------------------------------------------------------
-- 3. Compte ut_sqlacodegen
--    NOLOGIN par défaut — structurellement inutilisable hors fenêtre de
--    génération.
--    CONNECTION LIMIT 1 : une seule connexion simultanée autorisée.
--    PASSWORD NULL : aucun mot de passe initial — la SP le génère à la demande.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ut_sqlacodegen') THEN
        CREATE USER ut_sqlacodegen
            NOLOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            CONNECTION LIMIT 1
            PASSWORD NULL;
        GRANT r_sqlacodegen TO ut_sqlacodegen;
        RAISE NOTICE 'User ut_sqlacodegen créé.';
    ELSE
        RAISE NOTICE 'User ut_sqlacodegen existe déjà — ignoré.';
    END IF;
END;
$$;


-- -----------------------------------------------------------------------------
-- 4. Droits sur la base postgres elle-même
--    pg_catalog est accessible par défaut à tous — pas de GRANT nécessaire.
--    information_schema nécessite un GRANT explicite.
-- -----------------------------------------------------------------------------
GRANT CONNECT ON DATABASE postgres TO r_sqlacodegen;
GRANT USAGE ON SCHEMA information_schema TO r_sqlacodegen;
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO r_sqlacodegen;