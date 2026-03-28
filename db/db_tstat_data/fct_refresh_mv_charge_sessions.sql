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