-- =============================================================================
-- 02_sp_sqlacodegen.sql
-- =============================================================================
-- À exécuter UNE SEULE FOIS sur la base système "postgres" en tant que superuser.
--
-- Crée :
--   - public.sp_sqlacodegen(bool, text) : procédure d'activation/désactivation
--     de ut_sqlacodegen avec mot de passe éphémère généré aléatoirement.
--
-- Prérequis :
--   - 01_creation_roles.sql exécuté
--   - Être connecté à la base postgres en superuser
--   - Remplacer ut_baseref par le nom réel du compte applicatif si différent
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Procédure d'activation/désactivation
--
-- SECURITY DEFINER : s'exécute avec les droits du propriétaire (superuser).
-- L'appelant n'a pas besoin de droits ALTER USER.
--
-- sp_sqlacodegen(TRUE,  NULL) → active ut_sqlacodegen
--                                génère un mot de passe éphémère aléatoire
--                                retourne ce mot de passe dans p_password
--
-- sp_sqlacodegen(FALSE, NULL) → désactive ut_sqlacodegen
--                                invalide le mot de passe (PASSWORD NULL)
--                                p_password retourné à NULL
--
-- Le mot de passe est généré par gen_random_bytes(32) → base64 (~44 cars).
-- Imprévisible, jamais stocké, valide uniquement pendant la génération.
-- PASSWORD NULL à la désactivation : le compte est inutilisable même en cas
-- de réactivation manuelle accidentelle.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE public.sp_sqlacodegen(
    p_actif     BOOLEAN,
    INOUT p_password TEXT DEFAULT NULL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_pwd TEXT;
BEGIN
    IF p_actif THEN
        v_pwd := encode(gen_random_bytes(32), 'base64');
        EXECUTE format('ALTER USER ut_sqlacodegen LOGIN PASSWORD %L', v_pwd);
        p_password := v_pwd;
        RAISE NOTICE 'ut_sqlacodegen activé.';
    ELSE
        ALTER USER ut_sqlacodegen NOLOGIN;
        EXECUTE 'ALTER USER ut_sqlacodegen PASSWORD NULL';
        p_password := NULL;
        RAISE NOTICE 'ut_sqlacodegen désactivé.';
    END IF;
END;
$$;

-- Restreint l'exécution au seul compte applicatif
-- Remplacer ut_baseref par le compte applicatif réel si différent
REVOKE ALL ON PROCEDURE public.sp_sqlacodegen(BOOLEAN, TEXT) FROM PUBLIC;
GRANT EXECUTE ON PROCEDURE public.sp_sqlacodegen(BOOLEAN, TEXT) TO ut_tstat;