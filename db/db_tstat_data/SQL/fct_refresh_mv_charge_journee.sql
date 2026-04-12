-- =============================================================================
-- FONCTION : fct_refresh_mv_charge_journee
-- Rafraîchit mv_charge_journee (MV3).
-- Doit être appelée APRÈS fct_refresh_mv_charge_sessions_ext (MV2).
-- =============================================================================

CREATE OR REPLACE FUNCTION public.fct_refresh_mv_charge_journee()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_charge_journee;
END;
$$;

ALTER FUNCTION public.fct_refresh_mv_charge_journee()
    OWNER TO ut_tstat_admin;
ALTER FUNCTION public.fct_refresh_mv_charge_journee()
    SET search_path = public;
REVOKE ALL ON FUNCTION public.fct_refresh_mv_charge_journee() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.fct_refresh_mv_charge_journee() TO ut_tstat;


-- =============================================================================
-- MISE À JOUR : fct_refresh_all_charge_mv
-- Orchestre MV1 → MV2 → MV3 dans l'ordre.
-- Codes retour :
--   'OK'      — les trois MV rafraîchies avec succès
--   'ERR_MV1' — échec MV1 (MV2 et MV3 non tentées)
--   'ERR_MV2' — MV1 OK, échec MV2 (MV3 non tentée)
--   'ERR_MV3' — MV1 + MV2 OK, échec MV3
-- =============================================================================

CREATE OR REPLACE FUNCTION public.fct_refresh_all_charge_mv()
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN

    -- Étape 1 : MV1 — mv_charge_sessions
    BEGIN
        PERFORM public.fct_refresh_mv_charge_sessions();
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fct_refresh_all_charge_mv | MV1 échec : %', SQLERRM;
        RETURN 'ERR_MV1';
    END;

    -- Étape 2 : MV2 — mv_charge_sessions_ext
    BEGIN
        PERFORM public.fct_refresh_mv_charge_sessions_ext();
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fct_refresh_all_charge_mv | MV2 échec : %', SQLERRM;
        RETURN 'ERR_MV2';
    END;

    -- Étape 3 : MV3 — mv_charge_journee
    BEGIN
        PERFORM public.fct_refresh_mv_charge_journee();
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fct_refresh_all_charge_mv | MV3 échec : %', SQLERRM;
        RETURN 'ERR_MV3';
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
