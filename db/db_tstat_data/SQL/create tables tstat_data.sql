-- =============================================================================
-- db_tstat — Base de données statistiques Tesla
-- Instance PostgreSQL Freebox (même instance que db_baseref et db_tstat_admin)
-- =============================================================================
-- Prérequis : rôles r_crud, r_backup, ut_tstat_admin, ut_tstat, ut_backup
--             déjà créés sur l'instance.
-- Exécuter en tant que superuser (postgres) :
--   psql -U postgres -d postgres -f db_tstat_create.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- le point 1 création de la bdd a été supprimé car déjà effectué.
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- 2. TABLES
-- =============================================================================
-- Conventions :
--   T_   : table
--   IX_  : index
--   Colonnes préfixées par le triplet de leur table (VEH, SNP, CHG, DRV)
--   FK   : portent le nom de la colonne dans la table source
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 2.1  t_vehicle_veh
-- Copie synchronisée depuis db_tstat_admin.t_vehicle_veh
-- Source de vérité : db_tstat_admin (géré via BaseRef_Manager)
-- Synchronisation : tâche dédiée BaseRef_Manager — à implémenter
-- -----------------------------------------------------------------------------

CREATE TABLE public.t_vehicle_veh (
    veh_id              INTEGER         PRIMARY KEY,    -- Pas de SERIAL : synchronisé depuis db_tstat_admin
    veh_vin             VARCHAR(17)     NOT NULL UNIQUE,
    veh_displayname     VARCHAR(100)    NULL,
    veh_pollinginterval INTEGER         NOT NULL DEFAULT 300,
    veh_isactive        BOOLEAN         NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  public.t_vehicle_veh                      IS 'Véhicules — copie synchronisée depuis db_tstat_admin';
COMMENT ON COLUMN public.t_vehicle_veh.veh_id               IS 'Identifiant interne (synchronisé avec db_tstat_admin — pas d''auto-increment)';
COMMENT ON COLUMN public.t_vehicle_veh.veh_vin              IS 'Vehicle Identification Number (17 caractères)';
COMMENT ON COLUMN public.t_vehicle_veh.veh_displayname      IS 'Nom d''affichage du véhicule';
COMMENT ON COLUMN public.t_vehicle_veh.veh_pollinginterval  IS 'Intervalle de collecte en secondes (min. 60)';
COMMENT ON COLUMN public.t_vehicle_veh.veh_isactive         IS 'Véhicule actif pour la collecte';


-- -----------------------------------------------------------------------------
-- 2.2  t_snapshot_snp
-- Enveloppe de chaque appel API réussi
-- Une ligne = un appel = un instant T
-- Toutes les tables filles ont snp_id comme PK
-- -----------------------------------------------------------------------------

CREATE TABLE public.t_snapshot_snp (
    snp_id          SERIAL          PRIMARY KEY,
    veh_id          INTEGER         NOT NULL REFERENCES public.t_vehicle_veh(veh_id),
    snp_timestamp   TIMESTAMPTZ     NOT NULL,   -- Horodatage Tesla (converti depuis ms epoch)
    snp_collectedat TIMESTAMPTZ     NOT NULL,   -- Horodatage collecteur (maintenant_utc())
    snp_state       VARCHAR(20)     NOT NULL,   -- online / asleep / offline
    snp_odometer    NUMERIC(10,3)   NULL,       -- Kilométrage en miles (valeur brute Tesla)
    snp_firmware    VARCHAR(20)     NULL        -- Version firmware (ex : "2026.8")
);

COMMENT ON TABLE  public.t_snapshot_snp                 IS 'Enveloppe de chaque appel API — un enregistrement par snapshot';
COMMENT ON COLUMN public.t_snapshot_snp.snp_id          IS 'PK du snapshot — propagée comme PK dans toutes les tables filles';
COMMENT ON COLUMN public.t_snapshot_snp.veh_id          IS 'Véhicule associé -- FK → t_vehicle_veh';
COMMENT ON COLUMN public.t_snapshot_snp.snp_timestamp   IS 'Horodatage Tesla converti depuis ms epoch (UTC)';
COMMENT ON COLUMN public.t_snapshot_snp.snp_collectedat IS 'Horodatage d''enregistrement par le collecteur (UTC)';
COMMENT ON COLUMN public.t_snapshot_snp.snp_state       IS 'État du véhicule : online / asleep / offline';
COMMENT ON COLUMN public.t_snapshot_snp.snp_odometer    IS 'Kilométrage en miles -- (valeur brute Tesla — conversion à l''affichage)';
COMMENT ON COLUMN public.t_snapshot_snp.snp_firmware    IS 'Version du firmware embarqué';


-- -----------------------------------------------------------------------------
-- 2.3  t_charge_chg
-- Données de charge extraites du snapshot
-- PK = snp_id (relation 1-1 avec t_snapshot_snp)
-- Ligne créée uniquement si le véhicule est branché
-- -----------------------------------------------------------------------------

CREATE TABLE public.t_charge_chg (
    snp_id              INTEGER         PRIMARY KEY REFERENCES public.t_snapshot_snp(snp_id),
    chg_state           VARCHAR(20)     NOT NULL,   -- Charging / Complete / Disconnected / Stopped
    chg_batterylevel    SMALLINT        NULL,        -- % SOC affiché
    chg_usablelevel     SMALLINT        NULL,        -- % SOC utilisable (peut différer du SOC affiché)
    chg_range           NUMERIC(7,2)    NULL,        -- Autonomie en miles (valeur brute Tesla)
    chg_limitsoc        SMALLINT        NULL,        -- Limite de charge configurée (%)
    chg_power           SMALLINT        NULL,        -- Puissance en kW
    chg_voltage         SMALLINT        NULL,        -- Tension en Volts
    chg_current         SMALLINT        NULL,        -- Ampérage réel
    chg_rate            NUMERIC(5,1)    NULL,        -- Vitesse de charge (km/h d'autonomie ajoutée)
    chg_energyadded     NUMERIC(6,2)    NULL,        -- kWh ajoutés depuis le branchement
    chg_minutestofull   SMALLINT        NULL,        -- Minutes restantes avant charge complète
    chg_fastcharger     BOOLEAN         NULL,        -- Superchargeur / charge rapide
    chg_cabletype       VARCHAR(10)     NULL         -- Type de câble : IEC / CCS / ...
);

COMMENT ON TABLE  public.t_charge_chg                       IS 'Données de charge — une ligne par snapshot de charge';
COMMENT ON COLUMN public.t_charge_chg.snp_id                IS 'PK + FK → t_snapshot_snp (relation 1-1)';
COMMENT ON COLUMN public.t_charge_chg.chg_state             IS 'État de charge : Charging / Complete / Disconnected / Stopped';
COMMENT ON COLUMN public.t_charge_chg.chg_batterylevel      IS 'Niveau de batterie affiché (%)';
COMMENT ON COLUMN public.t_charge_chg.chg_usablelevel       IS 'Niveau de batterie utilisable (%) — peut différer du SOC affiché';
COMMENT ON COLUMN public.t_charge_chg.chg_range             IS 'Autonomie estimée en miles (valeur brute Tesla)';
COMMENT ON COLUMN public.t_charge_chg.chg_limitsoc          IS 'Limite de charge configurée par l''utilisateur (%)';
COMMENT ON COLUMN public.t_charge_chg.chg_power             IS 'Puissance de charge en kW';
COMMENT ON COLUMN public.t_charge_chg.chg_voltage           IS 'Tension en Volts';
COMMENT ON COLUMN public.t_charge_chg.chg_current           IS 'Intensité réelle en Ampères';
COMMENT ON COLUMN public.t_charge_chg.chg_rate              IS 'Vitesse de charge en km/h d''autonomie ajoutée';
COMMENT ON COLUMN public.t_charge_chg.chg_energyadded       IS 'Énergie ajoutée en kWh depuis le branchement';
COMMENT ON COLUMN public.t_charge_chg.chg_minutestofull     IS 'Temps restant avant charge complète (minutes)';
COMMENT ON COLUMN public.t_charge_chg.chg_fastcharger       IS 'TRUE si chargeur rapide (Superchargeur ou équivalent)';
COMMENT ON COLUMN public.t_charge_chg.chg_cabletype         IS 'Type de câble branché : IEC / CCS / ...';


-- -----------------------------------------------------------------------------
-- 2.4  t_drive_drv
-- Dernier état de conduite connu au moment du snapshot
-- PK = snp_id (relation 1-1 avec t_snapshot_snp)
-- Ligne créée uniquement quand shift_state est non null
-- -----------------------------------------------------------------------------

CREATE TABLE public.t_drive_drv (
    snp_id          INTEGER         PRIMARY KEY REFERENCES public.t_snapshot_snp(snp_id),
    drv_power       SMALLINT        NULL,   -- kW instantané (négatif = récupération d'énergie)
    drv_shiftstate  VARCHAR(5)      NULL,   -- P / D / R / N
    drv_speed       SMALLINT        NULL    -- Vitesse en km/h (null à l'arrêt)
);

COMMENT ON TABLE  public.t_drive_drv                    IS 'Dernier état de conduite connu — une ligne par snapshot de conduite';
COMMENT ON COLUMN public.t_drive_drv.snp_id             IS 'PK + FK → t_snapshot_snp (relation 1-1)';
COMMENT ON COLUMN public.t_drive_drv.drv_power          IS 'Puissance instantanée en kW (négative en récupération)';
COMMENT ON COLUMN public.t_drive_drv.drv_shiftstate     IS 'Position du sélecteur : P / D / R / N';
COMMENT ON COLUMN public.t_drive_drv.drv_speed          IS 'Vitesse en km/h (null si véhicule à l''arrêt)';


-- -----------------------------------------------------------------------------
-- 3. INDEX
-- -----------------------------------------------------------------------------

CREATE INDEX ix_snp_veh_id        ON public.t_snapshot_snp (veh_id);
CREATE INDEX ix_snp_timestamp     ON public.t_snapshot_snp (snp_timestamp DESC);
CREATE INDEX ix_snp_veh_timestamp ON public.t_snapshot_snp (veh_id, snp_timestamp DESC);
CREATE INDEX ix_chg_state         ON public.t_charge_chg   (chg_state);


-- -----------------------------------------------------------------------------
-- 4. DROITS
-- -----------------------------------------------------------------------------

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO r_crud;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO r_crud;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO r_backup;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO r_crud;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO r_crud;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO r_backup;


-- -----------------------------------------------------------------------------
-- FIN DU SCRIPT
-- -----------------------------------------------------------------------------