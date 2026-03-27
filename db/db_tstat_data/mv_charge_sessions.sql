-- =============================================================================
-- db_tstat_data — Tâche 1 — Vue matérialisée mv_charge_sessions
-- =============================================================================
-- Aucune modification de schéma.
-- Toutes les données nécessaires sont déjà dans t_charge_chg :
--   chg_batterylevel  → % batterie à chaque snapshot de charge
--   chg_energyadded   → kWh accumulés depuis le début de la session
--
-- Exécuter en tant que superuser ou ut_tstat_admin :
--   psql -U postgres -d db_tstat_data -f create_mv_charge_sessions.sql
-- =============================================================================


-- =============================================================================
-- 1. VUE MATÉRIALISÉE mv_charge_sessions
-- =============================================================================
--
-- Objectif :
--   Identifier chaque session de charge et calculer la capacité réelle
--   de la batterie par règle de trois :
--   capacite_kwh = energie_ajoutee / (soc_fin_pct - soc_debut_pct) * 100
--
-- Définition d'une rupture de session :
--   - Reset de chg_energyadded : la valeur retombe sous le snapshot précédent
--     (Tesla remet le compteur à zéro à chaque nouveau branchement)
--   - OU gap temporel > 4h entre deux snapshots de charge consécutifs
--     (filet de sécurité si le collecteur a manqué la déconnexion)
--
-- Filtres qualité :
--   - Variation SOC >= 5 points (filtre les sessions trop courtes)
--   - Énergie ajoutée > 1 kWh (filtre le bruit de mesure)
--   - Énergie totale > 0.1 kWh (exclut les sessions fantômes)
--
-- Usage dashboard — SOC estimé en kWh pour n'importe quel snapshot :
--
--   SELECT
--       s.snp_id,
--       s.snp_timestamp,
--       c.chg_batterylevel                                    AS soc_pct,
--       ROUND(
--           c.chg_batterylevel * cs.capacite_estimee_kwh / 100.0,
--       1)                                                    AS soc_kwh
--   FROM public.t_snapshot_snp  s
--   JOIN public.t_charge_chg    c  ON c.snp_id = s.snp_id
--   CROSS JOIN LATERAL (
--       SELECT capacite_estimee_kwh
--       FROM   public.mv_charge_sessions
--       WHERE  veh_id                  = s.veh_id
--       AND    fin_session             <= s.snp_timestamp
--       AND    capacite_estimee_kwh    IS NOT NULL
--       ORDER  BY fin_session DESC
--       LIMIT  1
--   ) cs;
--
-- =============================================================================

CREATE MATERIALIZED VIEW public.mv_charge_sessions AS

WITH snapshots_charge AS (
    -- Tous les snapshots de charge avec les valeurs du snapshot précédent
    SELECT
        s.snp_id,
        s.veh_id,
        s.snp_timestamp,
        c.chg_state,
        c.chg_batterylevel,
        c.chg_energyadded,
        LAG(c.chg_energyadded) OVER w AS prev_energyadded,
        LAG(s.snp_timestamp)   OVER w AS prev_timestamp
    FROM public.t_snapshot_snp s
    JOIN public.t_charge_chg   c ON c.snp_id = s.snp_id
    WHERE c.chg_state NOT IN ('Disconnected')
    WINDOW w AS (PARTITION BY s.veh_id ORDER BY s.snp_timestamp)
),

sessions_numerotees AS (
    -- Numérotation des sessions : SUM cumulatif des ruptures détectées.
    -- Chaque rupture incrémente le compteur → nouveau numéro de session.
    SELECT
        snp_id,
        veh_id,
        snp_timestamp,
        chg_state,
        chg_batterylevel,
        chg_energyadded,
        SUM(CASE
            WHEN prev_energyadded IS NULL
                THEN 1  -- premier snapshot de charge : début de session 1
            WHEN chg_energyadded < prev_energyadded
                THEN 1  -- reset compteur Tesla : nouveau branchement
            WHEN EXTRACT(EPOCH FROM (snp_timestamp - prev_timestamp)) > 14400
                THEN 1  -- gap > 4h : on considère une nouvelle session
            ELSE 0
        END) OVER (PARTITION BY veh_id ORDER BY snp_timestamp) AS session_num
    FROM snapshots_charge
),

sessions_agregees AS (
    -- Agrégation par session : une ligne par session de charge
    SELECT
        veh_id,
        session_num,
        MIN(snp_id)                                            AS snp_id_debut,
        MAX(snp_id)                                            AS snp_id_fin,
        MIN(snp_timestamp)                                     AS debut_session,
        MAX(snp_timestamp)                                     AS fin_session,
        MIN(chg_batterylevel)                                  AS soc_debut_pct,
        MAX(chg_batterylevel)                                  AS soc_fin_pct,
        MAX(chg_energyadded)                                   AS energie_ajoutee_kwh,
        -- État final : dernier chg_state chronologique de la session
        (ARRAY_AGG(chg_state ORDER BY snp_timestamp DESC))[1] AS etat_final
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
    ROUND(energie_ajoutee_kwh::NUMERIC, 2)                     AS energie_ajoutee_kwh,
    etat_final,
    -- Capacité réelle estimée par règle de trois.
    -- NULL si les données sont insuffisantes pour un calcul fiable.
    CASE
        WHEN (soc_fin_pct - soc_debut_pct) >= 5
         AND energie_ajoutee_kwh > 1.0
        THEN ROUND(
                energie_ajoutee_kwh::NUMERIC
                / (soc_fin_pct - soc_debut_pct)
                * 100.0,
             1)
        ELSE NULL
    END                                                         AS capacite_estimee_kwh

FROM sessions_agregees
WHERE energie_ajoutee_kwh > 0.1

WITH DATA;

COMMENT ON MATERIALIZED VIEW public.mv_charge_sessions IS
    'Sessions de charge détectées — capacité batterie estimée par règle de trois. '
    'REFRESH CONCURRENTLY déclenché par clsCollecteur sur transition Complete/Stopped.';

COMMENT ON COLUMN public.mv_charge_sessions.session_num          IS 'Numéro de session (compteur interne, repart de 1 après chaque REFRESH)';
COMMENT ON COLUMN public.mv_charge_sessions.soc_debut_pct        IS '% batterie au premier snapshot de la session';
COMMENT ON COLUMN public.mv_charge_sessions.soc_fin_pct          IS '% batterie au dernier snapshot de la session';
COMMENT ON COLUMN public.mv_charge_sessions.energie_ajoutee_kwh  IS 'MAX(chg_energyadded) — énergie totale ajoutée durant la session';
COMMENT ON COLUMN public.mv_charge_sessions.etat_final           IS 'Dernier chg_state connu : Complete / Stopped / Charging...';
COMMENT ON COLUMN public.mv_charge_sessions.capacite_estimee_kwh IS 'Capacité réelle estimée en kWh — NULL si variation SOC < 5 pts ou énergie < 1 kWh';


-- =============================================================================
-- 2. INDEX
-- =============================================================================

-- Index unique — requis pour REFRESH MATERIALIZED VIEW CONCURRENTLY.
-- Sans lui, le REFRESH pose un lock exclusif et bloque le dashboard.
CREATE UNIQUE INDEX ix_mv_cs_unique
    ON public.mv_charge_sessions (veh_id, session_num);

-- Index pour la jointure LATERAL du dashboard :
-- "dernière capacité estimée connue avant ce timestamp pour ce véhicule"
CREATE INDEX ix_mv_cs_veh_fin
    ON public.mv_charge_sessions (veh_id, fin_session DESC)
    WHERE capacite_estimee_kwh IS NOT NULL;


-- =============================================================================
-- 3. DROITS
-- =============================================================================

GRANT SELECT ON public.mv_charge_sessions TO r_crud;
GRANT SELECT ON public.mv_charge_sessions TO r_backup;


-- =============================================================================
-- FIN DU SCRIPT
-- =============================================================================