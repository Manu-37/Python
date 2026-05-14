-- Vue d'enrichissement IHM des colonnes
-- Utilisée par clsDBMetadata pour enrichir clsTableMetadata
-- depuis le référentiel IHM (libellés, largeurs, taf_code)
-- Pseudo-PK : (db_id, col_nom, lan_id)

CREATE VIEW ihm.v_col AS
SELECT
    db.db_id,
    db.db_code,
    rel.rel_nom,
    col.col_id,
    col.col_nom,
    col.col_largeur,
    col.col_actif,
    taf.taf_code,
    lco.lan_id,
    lco.lco_label,
    lco.lco_label_court,
    lco.lco_tooltip
FROM      ihm.t_db_db               db
JOIN      ihm.t_schema_sch          sch ON sch.db_id  = db.db_id
JOIN      ihm.t_relation_rel        rel ON rel.sch_id = sch.sch_id
JOIN      ihm.t_colonne_col         col ON col.rel_id = rel.rel_id
JOIN      ihm.t_type_affichage_taf  taf ON taf.taf_id = col.taf_id
LEFT JOIN ihm.t_libelle_colonne_lco lco ON lco.col_id = col.col_id
WHERE     rel.rel_actif = TRUE
  AND     sch.sch_actif = TRUE;
