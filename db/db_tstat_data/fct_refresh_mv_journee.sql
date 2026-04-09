-- =============================================================================
-- FONCTION : fct_refresh_mv_journee
-- Rafraîchit mv_journee (MV4) de façon autonome.
-- Utilisée par pg_cron (refresh quotidien à 1h) et appelable manuellement.
-- Doit être exécutée APRÈS mv_charge_journee (MV3) si un refresh complet est voulu —
-- dans ce cas, passer par fct_refresh_all_charge_mv() qui orchestre l'ordre.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.fct_refresh_mv_journee()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_journee;
END;
$$;

ALTER FUNCTION public.fct_refresh_mv_journee()
    OWNER TO ut_tstat_admin;
ALTER FUNCTION public.fct_refresh_mv_journee()
    SET search_path = public;
REVOKE ALL ON FUNCTION public.fct_refresh_mv_journee() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.fct_refresh_mv_journee() TO ut_tstat;


-- =============================================================================
-- MISE À JOUR : fct_refresh_all_charge_mv
-- Orchestre MV1 → MV2 → MV3 → MV4 dans l'ordre.
-- Déclenchée par le collecteur à chaque fin de session de charge.
-- Codes retour :
--   'OK'      — les quatre MV rafraîchies avec succès
--   'ERR_MV1' — échec MV1 (MV2, MV3, MV4 non tentées)
--   'ERR_MV2' — MV1 OK, échec MV2 (MV3, MV4 non tentées)
--   'ERR_MV3' — MV1 + MV2 OK, échec MV3 (MV4 non tentée)
--   'ERR_MV4' — MV1 + MV2 + MV3 OK, échec MV4
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

    -- Étape 4 : MV4 — mv_journee (dépend de MV3)
    BEGIN
        PERFORM public.fct_refresh_mv_journee();
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fct_refresh_all_charge_mv | MV4 échec : %', SQLERRM;
        RETURN 'ERR_MV4';
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


-- =============================================================================
-- PLANIFICATION pg_cron — refresh quotidien de mv_journee à 1h du matin
--
-- Pré-requis : pg_cron installé dans la base cible.
-- À exécuter UNE SEULE FOIS, connecté à la base de données tstat_data.
-- pg_cron s'exécute dans la base où il est installé — si pg_cron est dans
-- la base 'postgres', utiliser cron.schedule_in_database() à la place.
--
-- Pour vérifier que le job est enregistré :
--   SELECT * FROM cron.job;
--
-- Pour le désactiver :
--   SELECT cron.unschedule('refresh-mv-journee-quotidien');
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
    'refresh-mv-journee-quotidien',         -- nom du job (unique)
    '0 1 * * *',                            -- chaque jour à 1h00 UTC
    'SELECT public.fct_refresh_mv_journee()'
);
