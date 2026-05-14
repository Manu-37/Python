-- ================================================================
-- Migration : ajout env_id et bas_id sur t_db_db
-- Lien vers l'environnement et la base physique pour résolution
-- automatique de connexion via clsDBAManager dans l'explorateur.
-- Colonnes optionnelles (nullable) — aucun enregistrement existant
-- n'est impacté.
-- ================================================================

ALTER TABLE ihm.t_db_db
    ADD COLUMN env_id BIGINT,
    ADD COLUMN bas_id BIGINT,
    ADD CONSTRAINT fk_db_env FOREIGN KEY (env_id)
        REFERENCES public.t_environnement_env (env_id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_db_bas FOREIGN KEY (bas_id)
        REFERENCES public.t_base_bas          (bas_id) ON DELETE SET NULL;
