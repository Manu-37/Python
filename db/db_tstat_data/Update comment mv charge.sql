-- =============================================================================
-- MISE À JOUR DES COMMENTS — convention "Label court|Description tooltip"
-- Cibles : mv_charge_sessions, mv_charge_sessions_ext
-- Compatible get_col_label() / get_col_tooltip() de clsTableMetadata.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- mv_charge_sessions
-- -----------------------------------------------------------------------------

COMMENT ON COLUMN public.mv_charge_sessions.veh_id
    IS 'Véhicule|Identifiant du véhicule';

COMMENT ON COLUMN public.mv_charge_sessions.session_num
    IS 'N° session|Numéro de session (compteur interne, repart de 1 après chaque REFRESH FULL)';

COMMENT ON COLUMN public.mv_charge_sessions.snp_id_debut
    IS 'Snapshot début|Identifiant du premier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions.snp_id_fin
    IS 'Snapshot fin|Identifiant du dernier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions.debut_session
    IS 'Début|Horodatage du premier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions.fin_session
    IS 'Fin|Horodatage du dernier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions.soc_debut_pct
    IS 'SOC début %|% batterie au premier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions.soc_fin_pct
    IS 'SOC fin %|% batterie au dernier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions.energie_ajoutee_kwh
    IS 'Énergie ajoutée (kWh)|MAX(chg_energyadded) — énergie totale ajoutée durant la session';

COMMENT ON COLUMN public.mv_charge_sessions.etat_final
    IS 'État final|Dernier chg_state connu : Complete / Stopped / Charging...';

COMMENT ON COLUMN public.mv_charge_sessions.capacite_estimee_kwh
    IS 'Capacité estimée (kWh)|Capacité réelle estimée — NULL si variation SOC < 5 pts ou énergie < 1 kWh';

COMMENT ON COLUMN public.mv_charge_sessions.odometer_debut
    IS 'Odomètre début (mi)|Compteur kilométrique au premier snapshot de la session (miles bruts Tesla)';

COMMENT ON COLUMN public.mv_charge_sessions.odometer_fin
    IS 'Odomètre fin (mi)|Compteur kilométrique au dernier snapshot de la session (miles bruts Tesla)';


-- -----------------------------------------------------------------------------
-- mv_charge_sessions_ext
-- Colonnes héritées de mv_charge_sessions : mêmes labels.
-- Seule la colonne spécifique est commentée ici.
-- -----------------------------------------------------------------------------

COMMENT ON COLUMN public.mv_charge_sessions_ext.veh_id
    IS 'Véhicule|Identifiant du véhicule';

COMMENT ON COLUMN public.mv_charge_sessions_ext.session_num
    IS 'N° session|Numéro de session (compteur interne, repart de 1 après chaque REFRESH FULL)';

COMMENT ON COLUMN public.mv_charge_sessions_ext.snp_id_debut
    IS 'Snapshot début|Identifiant du premier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions_ext.snp_id_fin
    IS 'Snapshot fin|Identifiant du dernier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions_ext.debut_session
    IS 'Début|Horodatage du premier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions_ext.fin_session
    IS 'Fin|Horodatage du dernier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions_ext.soc_debut_pct
    IS 'SOC début %|% batterie au premier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions_ext.soc_fin_pct
    IS 'SOC fin %|% batterie au dernier snapshot de la session';

COMMENT ON COLUMN public.mv_charge_sessions_ext.energie_ajoutee_kwh
    IS 'Énergie ajoutée (kWh)|MAX(chg_energyadded) — énergie totale ajoutée durant la session';

COMMENT ON COLUMN public.mv_charge_sessions_ext.etat_final
    IS 'État final|Dernier chg_state connu : Complete / Stopped / Charging...';

COMMENT ON COLUMN public.mv_charge_sessions_ext.capacite_estimee_kwh
    IS 'Capacité estimée (kWh)|Capacité réelle estimée — NULL si variation SOC < 5 pts ou énergie < 1 kWh';

COMMENT ON COLUMN public.mv_charge_sessions_ext.odometer_debut
    IS 'Odomètre début (mi)|Compteur kilométrique au premier snapshot de la session (miles bruts Tesla)';

COMMENT ON COLUMN public.mv_charge_sessions_ext.odometer_fin
    IS 'Odomètre fin (mi)|Compteur kilométrique au dernier snapshot de la session (miles bruts Tesla)';

COMMENT ON COLUMN public.mv_charge_sessions_ext.miles_depuis_charge_precedente
    IS 'Distance depuis charge préc. (mi)|Distance parcourue depuis la fin de la session précédente (miles bruts Tesla) — NULL pour la 1ère session du véhicule';