-- =============================================================================
-- FONCTION : fct_refresh_mv_charge_sessions
-- Rafraîchit mv_charge_sessions (MV1).
-- Inchangée fonctionnellement — conservée pour compatibilité appelants existants.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.fct_refresh_mv_charge_sessions()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_charge_sessions;
END;
$$;

ALTER FUNCTION public.fct_refresh_mv_charge_sessions()
    OWNER TO ut_tstat_admin;
ALTER FUNCTION public.fct_refresh_mv_charge_sessions()
    SET search_path = public;
REVOKE ALL ON FUNCTION public.fct_refresh_mv_charge_sessions() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.fct_refresh_mv_charge_sessions() TO ut_tstat;


-- =============================================================================
-- FONCTION : fct_refresh_mv_charge_sessions_ext
-- Rafraîchit mv_charge_sessions_ext (MV2).
-- Doit être appelée APRES fct_refresh_mv_charge_sessions.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.fct_refresh_mv_charge_sessions_ext()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_charge_sessions_ext;
END;
$$;

ALTER FUNCTION public.fct_refresh_mv_charge_sessions_ext()
    OWNER TO ut_tstat_admin;
ALTER FUNCTION public.fct_refresh_mv_charge_sessions_ext()
    SET search_path = public;
REVOKE ALL ON FUNCTION public.fct_refresh_mv_charge_sessions_ext() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.fct_refresh_mv_charge_sessions_ext() TO ut_tstat;


-- =============================================================================
-- FONCTION : fct_refresh_all_charge_mv
-- Orchestrateur — rafraîchit MV1 puis MV2 dans l'ordre.
-- Retourne un code résultat exploitable par l'appelant Python :
--   'OK'         — les deux MV rafraîchies avec succès
--   'ERR_MV1'    — échec sur mv_charge_sessions        (MV2 non tentée)
--   'ERR_MV2'    — MV1 OK, échec sur mv_charge_sessions_ext
-- =============================================================================

CREATE OR REPLACE FUNCTION public.fct_refresh_all_charge_mv()
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN

    -- Étape 1 : MV1
    BEGIN
        PERFORM public.fct_refresh_mv_charge_sessions();
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fct_refresh_all_charge_mv | MV1 échec : %', SQLERRM;
        RETURN 'ERR_MV1';
    END;

    -- Étape 2 : MV2 (seulement si MV1 OK)
    BEGIN
        PERFORM public.fct_refresh_mv_charge_sessions_ext();
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fct_refresh_all_charge_mv | MV2 échec : %', SQLERRM;
        RETURN 'ERR_MV2';
    END;

    RETURN 'OK';

END;
$$;

ALTER FUNCTION public.fct_refresh_all_charge_mv()
    OWNER TO ut_tstat_admin;
ALTER FUNCTION public.fct_refresh_all_charge_mv()
    SET search_path = public;
REVOKE ALL ON FUNCTION public.fct_refresh_all_charge_mv() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.fct_refresh_all_charge_mv() TO ut_tstat;