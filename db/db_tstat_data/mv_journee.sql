-- =============================================================================
-- MATERIALIZED VIEW : mv_journee  (MV4)
-- Synthèse quotidienne complète — ancrée sur les snapshots, pas sur les charges.
-- Source principale : t_snapshot_snp  GROUP BY (veh_id, jour local Europe/Paris)
-- Source secondaire : mv_charge_journee (MV3) — LEFT JOIN pour l'énergie et
--                     la capacité des jours où une charge a eu lieu.
--
-- Colonnes :
--   veh_id               — véhicule
--   date_jour            — date locale Europe/Paris (= heure locale du conducteur)
--   km_journee           — (MAX(odometer) − MIN(odometer)) × 1,60934
--                          Capte tous les km du jour, y compris les jours sans charge.
--                          0 si un seul snapshot dans la journée.
--   nb_snapshots         — nombre de snapshots du jour (proxy de présence de données)
--   energie_ajoutee_kwh  — somme des énergies rechargées dans la journée (NULL si pas de charge)
--   capacite_estimee_kwh — dernière estimation de capacité batterie du jour (NULL si pas de charge)
--
-- Rattachement timezone :
--   snp_timestamp est stocké en UTC.
--   Le GROUP BY se fait sur DATE(snp_timestamp AT TIME ZONE 'Europe/Paris') pour que
--   les trajets du soir (> 23h UTC = > 00h Paris) tombent dans le bon jour local.
--   mv_charge_journee utilise DATE(debut_session) UTC — léger décalage possible pour
--   les sessions débutant entre 23h-00h UTC. Acceptable en l'état, documenté ici.
--
-- Données exclues :
--   Avant le 2026-03-25 — premiers jours de collecte incomplets (même convention MV3).
--
-- Dépendances :
--   t_snapshot_snp     — table source des snapshots
--   mv_charge_journee  — doit exister et être à jour avant le refresh de mv_journee
--
-- Rafraîchissement :
--   1. Via fct_refresh_all_charge_mv() — en fin de session de charge (MV4 = étape 4)
--   2. Via fct_refresh_mv_journee()    — planifié quotidiennement à 1h du matin
--      pour capter les jours sans charge (km présents, pas d'événement charge).
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS public.mv_journee;

CREATE MATERIALIZED VIEW public.mv_journee AS

WITH snp_jour AS (
    SELECT
        veh_id,
        DATE(snp_timestamp AT TIME ZONE 'Europe/Paris')             AS date_jour,
        ROUND(
            (MAX(snp_odometer) - MIN(snp_odometer))::NUMERIC
            * 1.60934,
            2
        )                                                           AS km_journee,
        COUNT(*)                                                    AS nb_snapshots
    FROM public.t_snapshot_snp
    WHERE snp_odometer IS NOT NULL
      AND DATE(snp_timestamp AT TIME ZONE 'Europe/Paris') >= '2026-03-25'
    GROUP BY
        veh_id,
        DATE(snp_timestamp AT TIME ZONE 'Europe/Paris')
)

SELECT
    s.veh_id,
    s.date_jour,
    s.km_journee,
    s.nb_snapshots,
    j.energie_ajoutee_kwh,
    j.capacite_estimee_kwh

FROM snp_jour s
LEFT JOIN public.mv_charge_journee j
    ON  j.veh_id   = s.veh_id
    AND j.date_jour = s.date_jour

WITH DATA;


-- =============================================================================
-- PROPRIÉTAIRE
-- =============================================================================

ALTER TABLE IF EXISTS public.mv_journee
    OWNER TO ut_tstat_admin;


-- =============================================================================
-- COMMENTAIRES
-- =============================================================================

COMMENT ON MATERIALIZED VIEW public.mv_journee IS
    'Synthèse quotidienne complète ancrée sur les snapshots (MV4). '
    'Présente une ligne par (veh_id, jour) dès qu''il y a au moins un snapshot, '
    'même les jours sans charge. Rattachement au jour local Europe/Paris. '
    'Rafraîchie en fin de session de charge ET quotidiennement à 1h via pg_cron.';

COMMENT ON COLUMN public.mv_journee.date_jour
    IS 'Date locale Europe/Paris — DATE(snp_timestamp AT TIME ZONE Europe/Paris).';

COMMENT ON COLUMN public.mv_journee.km_journee
    IS 'Kilométrage journalier = (MAX(odometer) − MIN(odometer)) × 1,60934. '
       '0 si un seul snapshot dans la journée. Basé sur odomètre brut Tesla (miles).';

COMMENT ON COLUMN public.mv_journee.nb_snapshots
    IS 'Nombre de snapshots dans la journée — proxy de présence/fiabilité des données.';

COMMENT ON COLUMN public.mv_journee.energie_ajoutee_kwh
    IS 'Énergie rechargée dans la journée (depuis mv_charge_journee). NULL si pas de charge.';

COMMENT ON COLUMN public.mv_journee.capacite_estimee_kwh
    IS 'Dernière estimation de capacité batterie du jour (depuis mv_charge_journee). '
       'NULL si pas de charge.';


-- =============================================================================
-- INDEX
-- =============================================================================

-- Index unique obligatoire pour REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX ix_mv_journee_unique
    ON public.mv_journee (veh_id, date_jour);

-- Index descendant pour les requêtes KPI (dernier jour, période glissante...)
CREATE INDEX ix_mv_journee_veh_date
    ON public.mv_journee (veh_id, date_jour DESC);


-- =============================================================================
-- DROITS
-- =============================================================================

GRANT SELECT ON public.mv_journee TO r_backup;
GRANT INSERT, DELETE, SELECT, UPDATE ON public.mv_journee TO r_crud;
GRANT ALL ON public.mv_journee TO ut_tstat_admin;
