-- =============================================================================
-- TABLE DE RÉFÉRENCE : t_dates_dat
-- Dimension calendaire — une ligne par jour de 2026-01-01 à 2035-12-31.
--
-- Colonnes :
--   dat_date         — clé primaire (DATE)
--   dat_annee        — année (ex. 2026)
--   dat_semestre     — semestre (1 ou 2)
--   dat_trimestre    — trimestre ISO (1 à 4)
--   dat_mois         — numéro de mois (1 à 12)
--   dat_semaine      — numéro de semaine ISO 8601 (1 à 53)
--                      Attention : la semaine 1 peut débuter en décembre de l'année précédente.
--   dat_jour_semaine — jour de la semaine en base 1 (EXTRACT(DOW) + 1)
--                      1 = dimanche, 2 = lundi, ..., 7 = samedi
--   dat_jour_nom     — libellé français du jour (lundi … dimanche)
--   dat_mois_nom     — libellé français du mois (janvier … décembre)
--   dat_est_weekend  — TRUE si samedi ou dimanche
--   dat_est_jour_ouvre — TRUE si lundi à vendredi (jours fériés non pris en compte)
--   dat_est_hiver    — TRUE si mois IN (11, 12, 1, 2, 3) — saison hivernale (recharge accrue)
--
-- Usage :
--   Jointure sur dat_date pour enrichir toute requête analytique datée.
--   Remplace les generate_series() dans les CTEs de séries temporelles.
--   Utilisée notamment dans la requête capacite_glissante() pour garantir
--   une série de dates continue.
--
-- Droits :
--   Lecture seule pour ut_tstat (compte applicatif).
--   Écriture réservée à ut_tstat_admin.
-- =============================================================================


-- =============================================================================
-- CRÉATION
-- =============================================================================

CREATE TABLE public.t_dates_dat (
    dat_date            DATE        PRIMARY KEY,
    dat_annee           SMALLINT    NOT NULL,
    dat_semestre        SMALLINT    NOT NULL,
    dat_trimestre       SMALLINT    NOT NULL,
    dat_mois            SMALLINT    NOT NULL,
    dat_semaine         SMALLINT    NOT NULL,
    dat_jour_semaine    SMALLINT    NOT NULL,
    dat_jour_nom        VARCHAR(15) NOT NULL,
    dat_mois_nom        VARCHAR(15) NOT NULL,
    dat_est_weekend     BOOLEAN     NOT NULL,
    dat_est_jour_ouvre  BOOLEAN     NOT NULL,
    dat_est_hiver       BOOLEAN     NOT NULL
);


-- =============================================================================
-- ALIMENTATION
-- =============================================================================

INSERT INTO public.t_dates_dat (
    dat_date,
    dat_annee,
    dat_semestre,
    dat_trimestre,
    dat_mois,
    dat_semaine,
    dat_jour_semaine,
    dat_jour_nom,
    dat_mois_nom,
    dat_est_weekend,
    dat_est_jour_ouvre,
    dat_est_hiver
)
SELECT
    d::date,
    EXTRACT(YEAR    FROM d)::smallint,
    CASE
        WHEN EXTRACT(MONTH FROM d) <= 6 THEN 1
        ELSE 2
    END,
    EXTRACT(QUARTER FROM d)::smallint,
    EXTRACT(MONTH   FROM d)::smallint,
    EXTRACT(WEEK    FROM d)::smallint,
    (EXTRACT(DOW    FROM d)::smallint + 1),
    CASE EXTRACT(DOW FROM d)
        WHEN 0 THEN 'dimanche'
        WHEN 1 THEN 'lundi'
        WHEN 2 THEN 'mardi'
        WHEN 3 THEN 'mercredi'
        WHEN 4 THEN 'jeudi'
        WHEN 5 THEN 'vendredi'
        WHEN 6 THEN 'samedi'
    END,
    CASE EXTRACT(MONTH FROM d)
        WHEN 1  THEN 'janvier'
        WHEN 2  THEN 'février'
        WHEN 3  THEN 'mars'
        WHEN 4  THEN 'avril'
        WHEN 5  THEN 'mai'
        WHEN 6  THEN 'juin'
        WHEN 7  THEN 'juillet'
        WHEN 8  THEN 'août'
        WHEN 9  THEN 'septembre'
        WHEN 10 THEN 'octobre'
        WHEN 11 THEN 'novembre'
        WHEN 12 THEN 'décembre'
    END,
    EXTRACT(DOW FROM d) IN (0, 6),
    EXTRACT(DOW FROM d) NOT IN (0, 6),
    EXTRACT(MONTH FROM d) IN (11, 12, 1, 2, 3)
FROM generate_series('2026-01-01'::date, '2035-12-31'::date, '1 day') AS d
ON CONFLICT DO NOTHING;


-- =============================================================================
-- INDEX
-- =============================================================================

CREATE INDEX idx_t_dates_dat_annee          ON public.t_dates_dat (dat_annee);
CREATE INDEX idx_t_dates_dat_semestre       ON public.t_dates_dat (dat_semestre);
CREATE INDEX idx_t_dates_dat_trimestre      ON public.t_dates_dat (dat_trimestre);
CREATE INDEX idx_t_dates_dat_mois           ON public.t_dates_dat (dat_mois);
CREATE INDEX idx_t_dates_dat_jour_semaine   ON public.t_dates_dat (dat_jour_semaine);
CREATE INDEX idx_t_dates_dat_est_weekend    ON public.t_dates_dat (dat_est_weekend);
CREATE INDEX idx_t_dates_dat_est_hiver      ON public.t_dates_dat (dat_est_hiver);


-- =============================================================================
-- PROPRIÉTAIRE
-- =============================================================================

ALTER TABLE public.t_dates_dat
    OWNER TO ut_tstat_admin;


-- =============================================================================
-- COMMENTAIRES
-- =============================================================================

COMMENT ON TABLE public.t_dates_dat IS
    'Dimension calendaire statique — une ligne par jour de 2026-01-01 à 2035-12-31. '
    'Utilisée comme spine de séries temporelles continues (remplace generate_series dans les CTEs). '
    'Jours fériés non modélisés — dat_est_jour_ouvre ne couvre que samedi/dimanche.';

COMMENT ON COLUMN public.t_dates_dat.dat_date           IS 'Clé primaire — date du jour (DATE).';
COMMENT ON COLUMN public.t_dates_dat.dat_annee          IS 'Année calendaire (ex. 2026).';
COMMENT ON COLUMN public.t_dates_dat.dat_semestre       IS 'Semestre : 1 (jan–juin) ou 2 (juil–déc).';
COMMENT ON COLUMN public.t_dates_dat.dat_trimestre      IS 'Trimestre ISO : 1 à 4.';
COMMENT ON COLUMN public.t_dates_dat.dat_mois           IS 'Numéro de mois : 1 (janvier) à 12 (décembre).';
COMMENT ON COLUMN public.t_dates_dat.dat_semaine        IS 'Numéro de semaine ISO 8601 (1 à 53). '
                                                           'La semaine 1 peut commencer en décembre de l''année précédente.';
COMMENT ON COLUMN public.t_dates_dat.dat_jour_semaine   IS 'Jour de la semaine en base 1 : 1=dimanche, 2=lundi, …, 7=samedi '
                                                           '(EXTRACT(DOW) + 1).';
COMMENT ON COLUMN public.t_dates_dat.dat_jour_nom       IS 'Libellé français du jour (lundi … dimanche).';
COMMENT ON COLUMN public.t_dates_dat.dat_mois_nom       IS 'Libellé français du mois (janvier … décembre).';
COMMENT ON COLUMN public.t_dates_dat.dat_est_weekend    IS 'TRUE si samedi ou dimanche.';
COMMENT ON COLUMN public.t_dates_dat.dat_est_jour_ouvre IS 'TRUE si lundi à vendredi. Jours fériés non pris en compte.';
COMMENT ON COLUMN public.t_dates_dat.dat_est_hiver      IS 'TRUE si mois IN (11, 12, 1, 2, 3) — saison hivernale, '
                                                           'corrélée à une consommation de recharge accrue.';


-- =============================================================================
-- DROITS
-- =============================================================================

GRANT SELECT                            ON public.t_dates_dat TO r_backup;
GRANT INSERT, DELETE, SELECT, UPDATE    ON public.t_dates_dat TO r_crud;
GRANT ALL                               ON public.t_dates_dat TO ut_tstat_admin;
GRANT SELECT                            ON public.t_dates_dat TO ut_tstat;
