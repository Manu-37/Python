-- =============================================================================
-- MATERIALIZED VIEW : mv_charge_sessions_ext
-- Extension de mv_charge_sessions — ajoute miles_depuis_charge_precedente
-- calculé par LAG sur odometer_fin de la session précédente.
--
-- Dépendance : mv_charge_sessions doit exister et être à jour.
-- Toujours rafraîchie APRÈS mv_charge_sessions via fct_refresh_all_charge_mv().
--
-- Les sessions fantômes sont déjà exclues en amont par mv_charge_sessions
-- (filtre MAX(chg_power) > 0). Cette vue ne contient que des sessions réelles.
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS public.mv_charge_sessions_ext;

CREATE MATERIALIZED VIEW public.mv_charge_sessions_ext AS

SELECT
    cs.veh_id,
    cs.session_num,
    cs.snp_id_debut,
    cs.snp_id_fin,
    cs.debut_session,
    cs.fin_session,
    cs.soc_debut_pct,
    cs.soc_fin_pct,
    cs.energie_ajoutee_kwh,
    cs.etat_final,
    cs.fastcharger,
    cs.puissance_max_kw,
    cs.puissance_moy_kw,
    cs.capacite_estimee_kwh,
    cs.odometer_debut,
    cs.odometer_fin,
    ROUND(
        cs.odometer_debut - LAG(cs.odometer_fin) OVER w,
        1
    ) AS miles_depuis_charge_precedente
FROM public.mv_charge_sessions cs
WINDOW w AS (PARTITION BY cs.veh_id ORDER BY cs.debut_session)

WITH DATA;


-- =============================================================================
-- PROPRIÉTAIRE
-- =============================================================================

ALTER TABLE IF EXISTS public.mv_charge_sessions_ext
    OWNER TO ut_tstat_admin;


-- =============================================================================
-- COMMENTAIRES
-- =============================================================================

COMMENT ON MATERIALIZED VIEW public.mv_charge_sessions_ext IS
    'Extension de mv_charge_sessions — ajoute miles_depuis_charge_precedente par LAG. '
    'Faits bruts uniquement — conversion km et calculs de consommation dans la couche stats. '
    'Sessions fantômes déjà exclues en amont par mv_charge_sessions (MAX(chg_power) > 0). '
    'Toujours rafraîchie APRÈS mv_charge_sessions via fct_refresh_all_charge_mv().';

COMMENT ON COLUMN public.mv_charge_sessions_ext.fastcharger
    IS 'TRUE si Superchargeur DC (hérité de mv_charge_sessions)';
COMMENT ON COLUMN public.mv_charge_sessions_ext.puissance_max_kw
    IS 'Puissance maximale atteinte pendant la session (kW)';
COMMENT ON COLUMN public.mv_charge_sessions_ext.puissance_moy_kw
    IS 'Puissance moyenne sur les snapshots avec chg_power > 0 (kW)';
COMMENT ON COLUMN public.mv_charge_sessions_ext.miles_depuis_charge_precedente
    IS 'Distance parcourue depuis la fin de la session précédente (miles bruts Tesla) — NULL pour la 1ère session du véhicule. Conversion km : × 1.609344.';


-- =============================================================================
-- INDEX
-- =============================================================================

CREATE UNIQUE INDEX ix_mv_cse_unique
    ON public.mv_charge_sessions_ext (veh_id, session_num);

CREATE INDEX ix_mv_cse_veh_debut
    ON public.mv_charge_sessions_ext (veh_id, debut_session DESC);


-- =============================================================================
-- DROITS
-- =============================================================================

GRANT SELECT ON public.mv_charge_sessions_ext TO r_backup;
GRANT INSERT, DELETE, SELECT, UPDATE ON public.mv_charge_sessions_ext TO r_crud;
GRANT ALL ON public.mv_charge_sessions_ext TO ut_tstat_admin;