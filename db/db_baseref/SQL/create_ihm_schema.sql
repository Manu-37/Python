-- ================================================================
-- Schéma IHM — Référentiel de présentation multilingue
-- Base cible : db_baseref
-- ================================================================

CREATE SCHEMA IF NOT EXISTS ihm;

-- ────────────────────────────────────────────────────
-- Fonction d'audit unique — BEFORE INSERT OR UPDATE
--
-- TG_TABLE_NAME : nom de la table ayant déclenché le trigger
--                 ex : 't_langue_lan' → triplet 'lan'
-- split_part / array_length : extraient le dernier segment
--                 après '_' = le triplet de la table
-- jsonb_build_object : construit {"lan_cree_le": now, ...}
-- jsonb_populate_record : fusionne ce jsonb dans NEW —
--                 seuls les champs nommés sont modifiés,
--                 le reste de NEW est conservé intact
-- ────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION ihm.fn_audit_ihm()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_triplet TEXT;
BEGIN
    v_triplet := split_part(TG_TABLE_NAME, '_',
                     array_length(string_to_array(TG_TABLE_NAME, '_'), 1));

    IF TG_OP = 'INSERT' THEN
        NEW := jsonb_populate_record(NEW, jsonb_build_object(
            v_triplet || '_cree_le',    NOW(),
            v_triplet || '_modifie_le', NOW()
        ));
    ELSIF TG_OP = 'UPDATE' THEN
        NEW := jsonb_populate_record(NEW, jsonb_build_object(
            v_triplet || '_modifie_le', NOW()
        ));
    END IF;
    RETURN NEW;
END;
$$;

-- ────────────────────────────────────────────────────
-- t_langue_lan
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_langue_lan (
    lan_id         BIGSERIAL    NOT NULL,
    lan_code       VARCHAR(32)  NOT NULL,
    lan_nom        VARCHAR(128) NOT NULL,
    lan_rtl        BOOLEAN      NOT NULL DEFAULT FALSE,
    lan_actif      BOOLEAN      NOT NULL DEFAULT TRUE,
    lan_ordre      INTEGER      NOT NULL DEFAULT 0,
    lan_cree_le    TIMESTAMPTZ  NOT NULL,
    lan_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_lan      PRIMARY KEY (lan_id),
    CONSTRAINT uq_lan_code UNIQUE (lan_code)
);
CREATE TRIGGER trg_audit_lan
    BEFORE INSERT OR UPDATE ON ihm.t_langue_lan
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_application_app
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_application_app (
    app_id          BIGSERIAL    NOT NULL,
    app_code        VARCHAR(32)  NOT NULL,
    app_nom         VARCHAR(128) NOT NULL,
    app_description VARCHAR(512),
    app_cree_le     TIMESTAMPTZ  NOT NULL,
    app_modifie_le  TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_app      PRIMARY KEY (app_id),
    CONSTRAINT uq_app_code UNIQUE (app_code)
);
CREATE TRIGGER trg_audit_app
    BEFORE INSERT OR UPDATE ON ihm.t_application_app
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_type_element_tel
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_type_element_tel (
    tel_id         BIGSERIAL    NOT NULL,
    tel_code       VARCHAR(32)  NOT NULL,
    tel_nom        VARCHAR(128) NOT NULL,
    tel_cree_le    TIMESTAMPTZ  NOT NULL,
    tel_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_tel      PRIMARY KEY (tel_id),
    CONSTRAINT uq_tel_code UNIQUE (tel_code)
);
CREATE TRIGGER trg_audit_tel
    BEFORE INSERT OR UPDATE ON ihm.t_type_element_tel
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_db_db
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_db_db (
    db_id          BIGSERIAL    NOT NULL,
    env_id         BIGINT,
    bas_id         BIGINT,
    db_code        VARCHAR(32)  NOT NULL,
    db_nom         VARCHAR(128) NOT NULL,
    db_description VARCHAR(512),
    db_cree_le     TIMESTAMPTZ  NOT NULL,
    db_modifie_le  TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_db      PRIMARY KEY (db_id),
    CONSTRAINT uq_db_code UNIQUE (db_code),
    CONSTRAINT fk_db_env  FOREIGN KEY (env_id) REFERENCES public.t_environnement_env (env_id) ON DELETE SET NULL,
    CONSTRAINT fk_db_bas  FOREIGN KEY (bas_id) REFERENCES public.t_base_bas          (bas_id) ON DELETE SET NULL
);
CREATE TRIGGER trg_audit_db
    BEFORE INSERT OR UPDATE ON ihm.t_db_db
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_type_relation_tre
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_type_relation_tre (
    tre_id         BIGSERIAL    NOT NULL,
    tre_code       VARCHAR(32)  NOT NULL,
    tre_nom        VARCHAR(128) NOT NULL,
    tre_cree_le    TIMESTAMPTZ  NOT NULL,
    tre_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_tre      PRIMARY KEY (tre_id),
    CONSTRAINT uq_tre_code UNIQUE (tre_code)
);
CREATE TRIGGER trg_audit_tre
    BEFORE INSERT OR UPDATE ON ihm.t_type_relation_tre
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_type_affichage_taf
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_type_affichage_taf (
    taf_id         BIGSERIAL    NOT NULL,
    taf_code       VARCHAR(32)  NOT NULL,
    taf_nom        VARCHAR(128) NOT NULL,
    taf_cree_le    TIMESTAMPTZ  NOT NULL,
    taf_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_taf      PRIMARY KEY (taf_id),
    CONSTRAINT uq_taf_code UNIQUE (taf_code)
);
CREATE TRIGGER trg_audit_taf
    BEFORE INSERT OR UPDATE ON ihm.t_type_affichage_taf
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_app_lan_nal  (liaison App ↔ Langue)
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_app_lan_nal (
    app_id         BIGINT      NOT NULL,
    lan_id         BIGINT      NOT NULL,
    nal_est_defaut BOOLEAN     NOT NULL DEFAULT FALSE,
    nal_cree_le    TIMESTAMPTZ NOT NULL,
    nal_modifie_le TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_nal     PRIMARY KEY (app_id, lan_id),
    CONSTRAINT fk_nal_app FOREIGN KEY (app_id) REFERENCES ihm.t_application_app (app_id),
    CONSTRAINT fk_nal_lan FOREIGN KEY (lan_id) REFERENCES ihm.t_langue_lan      (lan_id)
);
CREATE TRIGGER trg_audit_nal
    BEFORE INSERT OR UPDATE ON ihm.t_app_lan_nal
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_schema_sch
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_schema_sch (
    sch_id         BIGSERIAL    NOT NULL,
    db_id          BIGINT       NOT NULL,
    sch_nom        VARCHAR(128) NOT NULL,
    sch_actif      BOOLEAN      NOT NULL DEFAULT TRUE,
    sch_cree_le    TIMESTAMPTZ  NOT NULL,
    sch_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_sch    PRIMARY KEY (sch_id),
    CONSTRAINT fk_sch_db FOREIGN KEY (db_id) REFERENCES ihm.t_db_db (db_id),
    CONSTRAINT uq_sch    UNIQUE (db_id, sch_nom)
);
CREATE TRIGGER trg_audit_sch
    BEFORE INSERT OR UPDATE ON ihm.t_schema_sch
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_element_ele
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_element_ele (
    ele_id          BIGSERIAL    NOT NULL,
    app_id          BIGINT       NOT NULL,
    tel_id          BIGINT       NOT NULL,
    ele_cle         VARCHAR(32)  NOT NULL,
    ele_description VARCHAR(256),
    ele_cree_le     TIMESTAMPTZ  NOT NULL,
    ele_modifie_le  TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_ele     PRIMARY KEY (ele_id),
    CONSTRAINT fk_ele_app FOREIGN KEY (app_id) REFERENCES ihm.t_application_app  (app_id),
    CONSTRAINT fk_ele_tel FOREIGN KEY (tel_id) REFERENCES ihm.t_type_element_tel (tel_id),
    CONSTRAINT uq_ele     UNIQUE (app_id, ele_cle)
);
CREATE TRIGGER trg_audit_ele
    BEFORE INSERT OR UPDATE ON ihm.t_element_ele
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_relation_rel
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_relation_rel (
    rel_id         BIGSERIAL    NOT NULL,
    sch_id         BIGINT       NOT NULL,
    tre_id         BIGINT       NOT NULL,
    rel_nom        VARCHAR(128) NOT NULL,
    rel_actif      BOOLEAN      NOT NULL DEFAULT TRUE,
    rel_cree_le    TIMESTAMPTZ  NOT NULL,
    rel_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_rel     PRIMARY KEY (rel_id),
    CONSTRAINT fk_rel_sch FOREIGN KEY (sch_id) REFERENCES ihm.t_schema_sch       (sch_id) ON DELETE CASCADE,
    CONSTRAINT fk_rel_tre FOREIGN KEY (tre_id) REFERENCES ihm.t_type_relation_tre (tre_id),
    CONSTRAINT uq_rel     UNIQUE (sch_id, rel_nom)
);
CREATE TRIGGER trg_audit_rel
    BEFORE INSERT OR UPDATE ON ihm.t_relation_rel
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_libelle_relation_lre  (liaison Relation ↔ Langue)
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_libelle_relation_lre (
    rel_id         BIGINT       NOT NULL,
    lan_id         BIGINT       NOT NULL,
    lre_label      VARCHAR(128) NOT NULL,
    lre_tooltip    VARCHAR(512),
    lre_cree_le    TIMESTAMPTZ  NOT NULL,
    lre_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_lre     PRIMARY KEY (rel_id, lan_id),
    CONSTRAINT fk_lre_rel FOREIGN KEY (rel_id) REFERENCES ihm.t_relation_rel (rel_id) ON DELETE CASCADE,
    CONSTRAINT fk_lre_lan FOREIGN KEY (lan_id) REFERENCES ihm.t_langue_lan   (lan_id)
);
CREATE TRIGGER trg_audit_lre
    BEFORE INSERT OR UPDATE ON ihm.t_libelle_relation_lre
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_libelle_element_lel  (liaison Élément ↔ Langue)
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_libelle_element_lel (
    ele_id         BIGINT       NOT NULL,
    lan_id         BIGINT       NOT NULL,
    lel_label      VARCHAR(128) NOT NULL,
    lel_tooltip    VARCHAR(512),
    lel_cree_le    TIMESTAMPTZ  NOT NULL,
    lel_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_lel     PRIMARY KEY (ele_id, lan_id),
    CONSTRAINT fk_lel_ele FOREIGN KEY (ele_id) REFERENCES ihm.t_element_ele (ele_id) ON DELETE CASCADE,
    CONSTRAINT fk_lel_lan FOREIGN KEY (lan_id) REFERENCES ihm.t_langue_lan  (lan_id)
);
CREATE TRIGGER trg_audit_lel
    BEFORE INSERT OR UPDATE ON ihm.t_libelle_element_lel
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_colonne_col
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_colonne_col (
    col_id         BIGSERIAL    NOT NULL,
    rel_id         BIGINT       NOT NULL,
    taf_id         BIGINT       NOT NULL,
    col_nom        VARCHAR(128) NOT NULL,
    col_largeur    INTEGER,
    col_actif      BOOLEAN      NOT NULL DEFAULT TRUE,
    col_cree_le    TIMESTAMPTZ  NOT NULL,
    col_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_col     PRIMARY KEY (col_id),
    CONSTRAINT fk_col_rel FOREIGN KEY (rel_id) REFERENCES ihm.t_relation_rel      (rel_id) ON DELETE CASCADE,
    CONSTRAINT fk_col_taf FOREIGN KEY (taf_id) REFERENCES ihm.t_type_affichage_taf (taf_id),
    CONSTRAINT uq_col     UNIQUE (rel_id, col_nom)
);
CREATE TRIGGER trg_audit_col
    BEFORE INSERT OR UPDATE ON ihm.t_colonne_col
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_libelle_colonne_lco  (liaison Colonne ↔ Langue)
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_libelle_colonne_lco (
    col_id         BIGINT       NOT NULL,
    lan_id         BIGINT       NOT NULL,
    lco_label      VARCHAR(128) NOT NULL,
    lco_label_court VARCHAR(15),
    lco_tooltip    VARCHAR(512),
    lco_cree_le    TIMESTAMPTZ  NOT NULL,
    lco_modifie_le TIMESTAMPTZ  NOT NULL,
    CONSTRAINT pk_lco     PRIMARY KEY (col_id, lan_id),
    CONSTRAINT fk_lco_col FOREIGN KEY (col_id) REFERENCES ihm.t_colonne_col (col_id) ON DELETE CASCADE,
    CONSTRAINT fk_lco_lan FOREIGN KEY (lan_id) REFERENCES ihm.t_langue_lan  (lan_id)
);
CREATE TRIGGER trg_audit_lco
    BEFORE INSERT OR UPDATE ON ihm.t_libelle_colonne_lco
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ────────────────────────────────────────────────────
-- t_db_rapport_dbr
-- ────────────────────────────────────────────────────
CREATE TABLE ihm.t_db_rapport_dbr (
    dbr_id         BIGSERIAL   NOT NULL,
    db_id          BIGINT      NOT NULL,
    dbr_date       TIMESTAMPTZ NOT NULL,
    dbr_json       JSONB       NOT NULL,
    dbr_cree_le    TIMESTAMPTZ NOT NULL,
    dbr_modifie_le TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_dbr    PRIMARY KEY (dbr_id),
    CONSTRAINT fk_dbr_db FOREIGN KEY (db_id) REFERENCES ihm.t_db_db (db_id) ON DELETE CASCADE
);
CREATE TRIGGER trg_audit_dbr
    BEFORE INSERT OR UPDATE ON ihm.t_db_rapport_dbr
    FOR EACH ROW EXECUTE FUNCTION ihm.fn_audit_ihm();

-- ================================================================
-- Droits d'accès — schéma ihm
-- ================================================================

-- Accès au schéma
GRANT USAGE ON SCHEMA ihm TO r_crud;
GRANT USAGE ON SCHEMA ihm TO r_backup;

-- Droits sur les objets existants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES    IN SCHEMA ihm TO r_crud;
GRANT USAGE, SELECT                  ON ALL SEQUENCES IN SCHEMA ihm TO r_crud;
GRANT EXECUTE ON FUNCTION ihm.fn_audit_ihm()                        TO r_crud;

GRANT SELECT ON ALL TABLES    IN SCHEMA ihm TO r_backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA ihm TO r_backup;

-- Héritage automatique pour les futurs objets du schéma
ALTER DEFAULT PRIVILEGES IN SCHEMA ihm
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES    TO r_crud;
ALTER DEFAULT PRIVILEGES IN SCHEMA ihm
    GRANT USAGE, SELECT                  ON SEQUENCES TO r_crud;
ALTER DEFAULT PRIVILEGES IN SCHEMA ihm
    GRANT SELECT ON TABLES    TO r_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA ihm
    GRANT SELECT ON SEQUENCES TO r_backup;

-- ================================================================
-- Données de référence
-- ================================================================

INSERT INTO ihm.t_langue_lan (lan_code, lan_nom, lan_rtl, lan_actif) VALUES
    ('fr', 'Français', FALSE, TRUE),
    ('en', 'English',  FALSE, FALSE);

INSERT INTO ihm.t_application_app (app_code, app_nom, app_description) VALUES
    ('GLOBAL',          'Éléments globaux', 'Réservé — éléments UI partagés entre tous les projets'),
    ('BaseRef_Manager', 'BaseRef Manager',  NULL),
    ('tstat_analyse',   'Tstat Analyse',    NULL);

INSERT INTO ihm.t_type_element_tel (tel_code, tel_nom) VALUES
    ('BOUTON',  'Bouton'),
    ('ONGLET',  'Onglet'),
    ('TITRE',   'Titre de fenêtre'),
    ('SECTION', 'Section / groupe'),
    ('MENU',    'Élément de menu');

INSERT INTO ihm.t_type_relation_tre (tre_code, tre_nom) VALUES
    ('TABLE', 'Table'),
    ('VIEW',  'Vue'),
    ('MVIEW', 'Vue matérialisée');

INSERT INTO ihm.t_type_affichage_taf (taf_code, taf_nom) VALUES
    ('AUTO',      'Inféré automatiquement'),
    ('TEXTE',     'Texte'),
    ('NUMERIQUE', 'Numérique'),
    ('DATE',      'Date / Horodatage'),
    ('BOOLEEN',   'Booléen'),
    ('BINAIRE',   'Binaire / Chiffré');
