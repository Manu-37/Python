-- =============================================================================
-- MATERIALIZED VIEW : mv_charge_sessions
-- Sessions de charge détectées depuis t_snapshot_snp + t_charge_chg.
-- Capacité batterie estimée par règle de trois.
-- Odométre début/fin de session (en miles — conversion km à l'affichage).
-- REFRESH CONCURRENTLY via fct_refresh_mv_charge_sessions().
--
-- Filtre sessions fantômes (trois critères cumulatifs) :
--   1. energie_ajoutee_kwh > 1.0 : exclut les sessions où l'énergie calculée
--      (MAX - MIN de chg_energyadded) est inférieure à 1 kWh.
--      Justification : aucun chargeur domestique ne peut constituer une vraie
--      session en dessous de ce seuil ; les valeurs résiduelles de fluctuation
--      BMS (trickle après Complete, gap > 4h sans déconnexion) sont toutes < 1 kWh.
--   2. puissance_max > 0 : exclut les sessions où aucun watt n'a été échangé
--      (câble branché, BMS actif, chargeur ne délivrant rien).
--      Justification physique : chg_power > 0 ↔ chg_current > 0 ↔ charge réelle.
--   3. fin_session > debut_session : exclut les sessions à snapshot unique
--      (durée nulle). Tesla rapporte dans ce cas une énergie résiduelle du BMS,
--      pas une charge réelle — l'énergie affichée est celle accumulée avant
--      le branchement, pas pendant.
--
-- Détection de nouvelle session (sessions_numerotees) :
--   Un vrai début de session Tesla remet chg_energyadded à ~0 (le compteur repart
--   de zéro). Le critère "< 1.0 AND prev > 2.0" détecte uniquement ce cas.
--   Un critère sur la baisse relative (< prev - seuil) était trop fragile : Tesla
--   génère des fluctuations BMS de 0.3-0.8 kWh quand le véhicule est en Complete,
--   ce qui créait des sessions fantômes avec l'énergie résiduelle de la session
--   précédente comme valeur MAX.
--
-- Début de session :
--   debut_session, snp_id_debut, odometer_debut et soc_debut_pct sont calculés
--   sur le premier snapshot avec chg_power > 0 — heure de début de charge
--   réelle, pas heure de branchement (qui peut précéder de plusieurs minutes).
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS public.mv_charge_sessions CASCADE;

CREATE MATERIALIZED VIEW public.mv_charge_sessions AS

WITH snapshots_charge AS (
    -- Tous les snapshots de charge avec les valeurs du snapshot précédent
    SELECT
        s.snp_id,
        s.veh_id,
        s.snp_timestamp,
        s.snp_odometer,
        c.chg_state,
        c.chg_batterylevel,
        c.chg_energyadded,
        c.chg_power,
        c.chg_fastcharger,
        LAG(c.chg_energyadded) OVER w AS prev_energyadded,
        LAG(s.snp_timestamp)   OVER w AS prev_timestamp
    FROM public.t_snapshot_snp s
    JOIN public.t_charge_chg   c ON c.snp_id = s.snp_id
    WHERE c.chg_state NOT IN ('Disconnected')
    WINDOW w AS (PARTITION BY s.veh_id ORDER BY s.snp_timestamp)
),

sessions_numerotees AS (
    SELECT
        snp_id,
        veh_id,
        snp_timestamp,
        snp_odometer,
        chg_state,
        chg_batterylevel,
        chg_energyadded,
        chg_power,
        chg_fastcharger,
        SUM(CASE
            WHEN prev_energyadded IS NULL
                THEN 1
            WHEN chg_energyadded < 1.0 AND prev_energyadded > 2.0
                THEN 1
            WHEN EXTRACT(EPOCH FROM (snp_timestamp - prev_timestamp)) > 14400
                THEN 1
            ELSE 0
        END) OVER (PARTITION BY veh_id ORDER BY snp_timestamp) AS session_num
    FROM snapshots_charge
),

sessions_agregees AS (
    SELECT
        veh_id,
        session_num,
        -- Début de session : premier snapshot avec chg_power > 0
        -- (heure de début de charge réelle, pas heure de branchement)
        MIN(CASE WHEN chg_power > 0 THEN snp_id END)           AS snp_id_debut,
        MAX(snp_id)                                             AS snp_id_fin,
        MIN(CASE WHEN chg_power > 0 THEN snp_timestamp END)    AS debut_session,
        MAX(snp_timestamp)                                      AS fin_session,
        MIN(CASE WHEN chg_power > 0 THEN chg_batterylevel END) AS soc_debut_pct,
        MAX(chg_batterylevel)                                   AS soc_fin_pct,
        MAX(chg_energyadded) - MIN(chg_energyadded)             AS energie_ajoutee_kwh,
        MAX(chg_power)                                                    AS puissance_max,
        BOOL_OR(chg_fastcharger)                                          AS fastcharger,
        AVG(chg_power) FILTER (WHERE chg_power > 0)                       AS puissance_moy,
        (ARRAY_AGG(chg_state ORDER BY snp_timestamp DESC))[1]             AS etat_final,
        -- Odométre début : premier snapshot avec chg_power > 0
        -- Odométre fin   : dernier snapshot de la session (tous états)
        (ARRAY_AGG(snp_odometer ORDER BY
            CASE WHEN chg_power > 0 THEN snp_timestamp END ASC
            NULLS LAST
        ))[1]                                                   AS odometer_debut,
        (ARRAY_AGG(snp_odometer ORDER BY snp_timestamp DESC))[1] AS odometer_fin
    FROM sessions_numerotees
    GROUP BY veh_id, session_num
)

SELECT
    veh_id,
    session_num,
    snp_id_debut,
    snp_id_fin,
    debut_session,
    fin_session,
    soc_debut_pct,
    soc_fin_pct,
    ROUND(energie_ajoutee_kwh::NUMERIC, 2)                      AS energie_ajoutee_kwh,
    etat_final,
    fastcharger,
    puissance_max                                               AS puissance_max_kw,
    ROUND(puissance_moy::NUMERIC, 1)                            AS puissance_moy_kw,
    CASE
        WHEN (soc_fin_pct - soc_debut_pct) >= 5
         AND energie_ajoutee_kwh > 1.0
        THEN ROUND(
                energie_ajoutee_kwh::NUMERIC
                / (soc_fin_pct - soc_debut_pct)
                * 100.0,
             1)
        ELSE NULL
    END                                                          AS capacite_estimee_kwh,
    -- Odométre brut en miles — conversion km à l'affichage (× 1.609344)
    odometer_debut,
    odometer_fin

FROM sessions_agregees
WHERE energie_ajoutee_kwh > 1.0
  AND puissance_max > 0
  -- puissance_max > 0 : exclut les sessions fantômes
  -- (câble branché, BMS actif, zéro watt échangé)
  AND fin_session > debut_session
  -- fin_session > debut_session : exclut les sessions à snapshot unique
  -- (durée nulle — Tesla rapporte une énergie résiduelle du BMS,
  --  pas une charge réelle)

WITH DATA;


-- =============================================================================
-- COMMENTAIRES
-- =============================================================================

COMMENT ON MATERIALIZED VIEW public.mv_charge_sessions IS
    'Sessions de charge réelles — capacité batterie estimée par règle de trois. '
    'Odométre en miles (début et fin de session). '
    'Sessions fantômes exclues via MAX(chg_power) > 0. '
    'debut_session = premier snapshot avec chg_power > 0 (début de charge réelle, '
    'pas branchement). '
    'REFRESH CONCURRENTLY déclenché par fct_refresh_all_charge_mv() sur transition Complete/Stopped.';

COMMENT ON COLUMN public.mv_charge_sessions.session_num          IS 'Numéro de session (compteur interne, repart de 1 après chaque REFRESH FULL)';
COMMENT ON COLUMN public.mv_charge_sessions.soc_debut_pct        IS '% batterie au premier snapshot avec chg_power > 0 (début de charge réelle)';
COMMENT ON COLUMN public.mv_charge_sessions.soc_fin_pct          IS '% batterie au dernier snapshot de la session';
COMMENT ON COLUMN public.mv_charge_sessions.energie_ajoutee_kwh  IS 'MAX - MIN(chg_energyadded) — croissance du compteur dans la session (évite les valeurs résiduelles héritées de la session précédente quand Tesla ne remet pas le compteur à zéro)';
COMMENT ON COLUMN public.mv_charge_sessions.etat_final           IS 'Dernier chg_state connu : Complete / Stopped / Charging...';
COMMENT ON COLUMN public.mv_charge_sessions.capacite_estimee_kwh IS 'Capacité réelle estimée en kWh — NULL si variation SOC < 5 pts ou énergie < 1 kWh';
COMMENT ON COLUMN public.mv_charge_sessions.odometer_debut       IS 'Kilométrage au premier snapshot avec chg_power > 0 (miles bruts Tesla)';
COMMENT ON COLUMN public.mv_charge_sessions.odometer_fin         IS 'Kilométrage au dernier snapshot de la session (miles bruts Tesla)';
COMMENT ON COLUMN public.mv_charge_sessions.fastcharger          IS 'TRUE si au moins un snapshot de la session avait chg_fastcharger = TRUE (Superchargeur DC)';
COMMENT ON COLUMN public.mv_charge_sessions.puissance_max_kw     IS 'Puissance maximale atteinte pendant la session (kW)';
COMMENT ON COLUMN public.mv_charge_sessions.puissance_moy_kw     IS 'Puissance moyenne sur les snapshots avec chg_power > 0 (kW)';


-- =============================================================================
-- INDEX
-- =============================================================================

CREATE UNIQUE INDEX ix_mv_cs_unique
    ON public.mv_charge_sessions (veh_id, session_num);

CREATE INDEX ix_mv_cs_veh_fin
    ON public.mv_charge_sessions (veh_id, fin_session DESC)
    WHERE capacite_estimee_kwh IS NOT NULL;


-- =============================================================================
-- DROITS
-- =============================================================================

GRANT SELECT ON public.mv_charge_sessions TO r_crud;
GRANT SELECT ON public.mv_charge_sessions TO r_backup;