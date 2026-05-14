-- ================================================================
-- Création : t_db_rapport_dbr
-- Rapports différentiels DB réelle ↔ catalogue BaseRef,
-- persistés en JSON. Un enregistrement par scan validé.
-- ================================================================

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
