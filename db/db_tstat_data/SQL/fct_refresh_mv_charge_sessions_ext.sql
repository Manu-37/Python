-- View: public.mv_charge_sessions_ext

-- DROP MATERIALIZED VIEW IF EXISTS public.mv_charge_sessions_ext;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_charge_sessions_ext
TABLESPACE pg_default
AS
 SELECT cs.veh_id,
    cs.session_num,
    cs.snp_id_debut,
    cs.snp_id_fin,
    cs.debut_session,
    cs.fin_session,
    cs.soc_debut_pct,
    cs.soc_fin_pct,
    cs.energie_ajoutee_kwh,
    cs.etat_final,
    cs.capacite_estimee_kwh,
    cs.odometer_debut,
    cs.odometer_fin,
    round(cs.odometer_debut - lag(cs.odometer_fin) OVER w, 1) AS miles_depuis_charge_precedente
   FROM mv_charge_sessions cs
  WINDOW w AS (PARTITION BY cs.veh_id ORDER BY cs.debut_session)
WITH DATA;

ALTER TABLE IF EXISTS public.mv_charge_sessions_ext
    OWNER TO ut_tstat_admin;

COMMENT ON MATERIALIZED VIEW public.mv_charge_sessions_ext
    IS 'Extension de mv_charge_sessions — ajoute miles_depuis_charge_precedente par LAG. Faits bruts uniquement — conversion km et calculs de consommation dans la couche stats. Toujours rafraîchie APRES mv_charge_sessions via fct_refresh_all_charge_mv().';

GRANT SELECT ON TABLE public.mv_charge_sessions_ext TO r_backup;
GRANT INSERT, DELETE, SELECT, UPDATE ON TABLE public.mv_charge_sessions_ext TO r_crud;
GRANT ALL ON TABLE public.mv_charge_sessions_ext TO ut_tstat_admin;

CREATE UNIQUE INDEX ix_mv_cse_unique
    ON public.mv_charge_sessions_ext USING btree
    (veh_id, session_num)
    TABLESPACE pg_default;

CREATE INDEX ix_mv_cse_veh_debut
    ON public.mv_charge_sessions_ext USING btree
    (veh_id, debut_session DESC)
    TABLESPACE pg_default;
COMMENT ON COLUMN public.mv_charge_sessions_ext.miles_depuis_charge_precedente
    IS 'Distance parcourue depuis la fin de la session précédente (miles bruts Tesla) — NULL pour la 1ère session du véhicule. Conversion km : × 1.60934.';