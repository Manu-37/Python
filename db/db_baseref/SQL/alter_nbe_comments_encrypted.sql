-- =============================================================================
-- alter_nbe_comments_encrypted.sql
-- =============================================================================
-- Marque les colonnes chiffrées de t_bas_env_nbe avec le commentaire 'encrypted'.
-- Utilisé par regenerer_modeles.py pour injecter EncryptedBytes (TypeDecorator)
-- à la place de LargeBinary dans le fichier généré.
--
-- Convention : toute colonne BYTEA portant le commentaire 'encrypted' sera
-- automatiquement typée EncryptedBytes lors de la régénération.
-- Les colonnes BYTEA sans ce commentaire (ex: logo, image) restent LargeBinary.
--
-- Base cible : db_baseref
-- Schéma     : public
-- Table      : t_bas_env_nbe
-- =============================================================================
 
-- Connexion de base
COMMENT ON COLUMN public.t_bas_env_nbe.nbe_host         IS 'encrypted';
COMMENT ON COLUMN public.t_bas_env_nbe.nbe_user         IS 'encrypted';
COMMENT ON COLUMN public.t_bas_env_nbe.nbe_pwd          IS 'encrypted';
 
-- SSH
COMMENT ON COLUMN public.t_bas_env_nbe.nbe_ssh_host     IS 'encrypted';
COMMENT ON COLUMN public.t_bas_env_nbe.nbe_ssh_user     IS 'encrypted';
COMMENT ON COLUMN public.t_bas_env_nbe.nbe_ssh_key_path IS 'encrypted';
 