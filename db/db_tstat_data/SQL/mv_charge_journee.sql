-- =============================================================================
-- MATERIALIZED VIEW : mv_charge_journee
-- Synthèse quotidienne des sessions de charge.
-- Source : mv_charge_sessions_ext (MV2).
--
-- Règle de rattachement :
--   Une session appartient au jour de sa date de DÉBUT (debut_session UTC).
--   La fin peut déborder sur j+1 — fin_session MAX reflète la réalité.
--
-- Plusieurs sessions dans la même journée sont agrégées :
--   session_num_debut / fin : MIN / MAX de session_num
--   snp_id_debut / fin      : MIN de snp_id_debut / MAX de snp_id_fin
--   soc_debut_pct           : SOC début de la première session du jour
--   soc_fin_pct             : SOC fin de la dernière session du jour
--   energie_ajoutee_kwh     : SOMME des énergies
--   odometer_debut / fin    : odomètre de la première / dernière session
--   miles_depuis_charge_prec: SOMME des distances inter-charges (NULL si
--                              toutes les sessions du jour n'ont pas de valeur)
--   capacite_estimee_kwh    : dernière capacité estimée non NULL du jour
--
-- Dépendance : mv_charge_sessions_ext doit exister et être à jour.
-- Rafraîchie APRÈS mv_charge_sessions_ext via fct_refresh_all_charge_mv().
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS public.mv_charge_journee;

CREATE MATERIALIZED VIEW public.mv_charge_journee AS

WITH sessions_du_jour AS (
    SELECT
        veh_id,
        DATE(debut_session)                                             AS date_jour,
        session_num,
        snp_id_debut,
        snp_id_fin,
        debut_session,
        fin_session,
        soc_debut_pct,
        soc_fin_pct,
        energie_ajoutee_kwh,
        odometer_debut,
        odometer_fin,
        miles_depuis_charge_precedente,
        capacite_estimee_kwh,
        -- Rang ascendant / descendant dans la journée — pour récupérer
        -- les valeurs de début (première session) et de fin (dernière session)
        ROW_NUMBER() OVER (
            PARTITION BY veh_id, DATE(debut_session)
            ORDER BY debut_session ASC
        )                                                               AS rn_asc,
        ROW_NUMBER() OVER (
            PARTITION BY veh_id, DATE(debut_session)
            ORDER BY debut_session DESC
        )                                                               AS rn_desc
    FROM public.mv_charge_sessions_ext
    -- Exclusion des premières journées de collecte — données incomplètes,
    -- pas de session précédente disponible pour calculer les distances.
    -- 2026-03-23 : premier jour de collecte (données partielles)
    -- 2026-03-24 : deuxième jour, incomplet par précaution
    WHERE DATE(debut_session) >= '2026-03-25'
)

SELECT
    veh_id,
    date_jour,
    MIN(session_num)                                                    AS session_num_debut,
    MAX(session_num)                                                    AS session_num_fin,
    MIN(snp_id_debut)                                                   AS snp_id_debut,
    MAX(snp_id_fin)                                                     AS snp_id_fin,
    MIN(debut_session)                                                  AS debut_session,
    MAX(fin_session)                                                    AS fin_session,
    MAX(CASE WHEN rn_asc  = 1 THEN soc_debut_pct END)                  AS soc_debut_pct,
    MAX(CASE WHEN rn_desc = 1 THEN soc_fin_pct   END)                  AS soc_fin_pct,
    ROUND(SUM(energie_ajoutee_kwh)::NUMERIC, 2)                        AS energie_ajoutee_kwh,
    MAX(CASE WHEN rn_asc  = 1 THEN odometer_debut END)                 AS odometer_debut,
    MAX(CASE WHEN rn_desc = 1 THEN odometer_fin   END)                 AS odometer_fin,
    ROUND(SUM(miles_depuis_charge_precedente)::NUMERIC, 1)             AS miles_depuis_charge_precedente,
    -- Dernière capacité estimée non NULL de la journée
    (ARRAY_AGG(
        capacite_estimee_kwh
        ORDER BY debut_session DESC
    ) FILTER (WHERE capacite_estimee_kwh IS NOT NULL))[1]              AS capacite_estimee_kwh

FROM sessions_du_jour
GROUP BY veh_id, date_jour

WITH DATA;


-- =============================================================================
-- PROPRIÉTAIRE
-- =============================================================================

ALTER TABLE IF EXISTS public.mv_charge_journee
    OWNER TO ut_tstat_admin;


-- =============================================================================
-- COMMENTAIRES
-- =============================================================================

COMMENT ON MATERIALIZED VIEW public.mv_charge_journee IS
    'Synthèse quotidienne des sessions de charge. '
    'Rattachement au jour de debut_session (UTC). '
    'Plusieurs sessions dans la journée sont agrégées — énergie sommée, '
    'SOC et odomètre pris sur la première/dernière session du jour. '
    'Rafraîchie après mv_charge_sessions_ext via fct_refresh_all_charge_mv().';

COMMENT ON COLUMN public.mv_charge_journee.date_jour
    IS 'Date UTC de debut_session — clé de rattachement journalier.';
COMMENT ON COLUMN public.mv_charge_journee.energie_ajoutee_kwh
    IS 'Somme des énergies ajoutées sur toutes les sessions du jour.';
COMMENT ON COLUMN public.mv_charge_journee.miles_depuis_charge_precedente
    IS 'Somme des distances inter-charges du jour (miles bruts). NULL si aucune valeur disponible.';
COMMENT ON COLUMN public.mv_charge_journee.capacite_estimee_kwh
    IS 'Dernière capacité estimée non NULL parmi les sessions du jour.';


-- =============================================================================
-- INDEX
-- =============================================================================

CREATE UNIQUE INDEX ix_mv_cj_unique
    ON public.mv_charge_journee (veh_id, date_jour);

CREATE INDEX ix_mv_cj_veh_date
    ON public.mv_charge_journee (veh_id, date_jour DESC);


-- =============================================================================
-- DROITS
-- =============================================================================

GRANT SELECT ON public.mv_charge_journee TO r_backup;
GRANT INSERT, DELETE, SELECT, UPDATE ON public.mv_charge_journee TO r_crud;
GRANT ALL ON public.mv_charge_journee TO ut_tstat_admin;
