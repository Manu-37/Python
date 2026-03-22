"""
clsCollecteur.py

Logique principale du collecteur Tesla.

Responsabilité :
    - Interroger l'API Tesla via clsTeslaVehicle
    - Mapper la réponse vers clsSNP, clsCHG, clsDRV
    - Persister en base dans une transaction unique
    - Gérer les retries si la fréquence le permet
    - Comptabiliser les échecs consécutifs et alerter

Contrat de résultat :
    run() retourne un dict :
        {"succes": True,  "snp_id": int}         — snapshot enregistré
        {"succes": False, "erreur": "message"}    — échec après retries éventuels
        {"succes": None}                          — fréquence non atteinte, rien à faire

Ce collecteur ne sait pas s'il doit être lancé — c'est clsFrequenceManager qui décide.
clsCollecteur est appelé uniquement si doit_interroger() == True.
"""

import time
from datetime import datetime, timezone

from sysclasses.clsLOG               import clsLOG
from sysclasses.tools                import Tools

from projets.shared.tesla.clsTeslaAuth    import clsTeslaAuth
from projets.shared.tesla.clsTeslaVehicle import clsTeslaVehicle

from db.db_tstat_data.public.clsSNP  import clsSNP
from db.db_tstat_data.public.clsCHG  import clsCHG
from db.db_tstat_data.public.clsDRV  import clsDRV
from db.db_tstat_data.public.clsVEH  import clsVEH as clsVEH_Data


# --------------------------------------------------
# États de charge qui indiquent un branchement actif
# --------------------------------------------------
ETATS_BRANCHE = ("Charging", "Complete", "Stopped", "NoPower")


class clsCollecteur:
    """
    Collecteur de données Tesla.

    Usage :
        collecteur = clsCollecteur(veh_id=1, params=oIni.collecteur_params)
        resultat   = collecteur.run(freq_retry_active=True)
    """

    def __init__(self, veh_id: int, params: dict):
        """
        Paramètres :
            veh_id : identifiant du véhicule dans db_tstat_admin ET db_tstat_data
            params : dict issu de clsINICollecteur.collecteur_params
        """
        self._log     = clsLOG()
        self._veh_id  = veh_id
        self._params  = params

        # Chargement du véhicule depuis db_tstat_data — référence FK pour les snapshots
        self._oVEH = clsVEH_Data(veh_id=veh_id)

        if not self._oVEH.veh_vin:
            raise ValueError(
                f"clsCollecteur | Véhicule veh_id={veh_id} introuvable "
                "dans db_tstat_data.t_vehicle_veh."
            )

        # Initialisation de l'authentification Tesla
        # clsTeslaAuth charge les tokens depuis db_tstat_admin.t_teslatoken_ttk
        # Le veh_id dans db_tstat_admin est garanti identique (synchronisation)
        self._auth    = clsTeslaAuth(veh_id=veh_id)
        self._vehicle = clsTeslaVehicle(self._auth)

        self._log.info(
            f"clsCollecteur | Initialisé pour {self._oVEH.veh_displayname} "
            f"(VIN={self._oVEH.veh_vin})"
        )

    # --------------------------------------------------
    # Point d'entrée principal
    # --------------------------------------------------

    def run(self, freq_retry_active: bool = False) -> dict:
        """
        Exécute un cycle de collecte complet.

        Paramètres :
            freq_retry_active : si True, active le mécanisme de retry en cas d'échec.
                                Fourni par clsFrequenceManager.freq_retry_active.

        Retourne :
            {"succes": True,  "snp_id": int}
            {"succes": False, "erreur": "message"}
        """
        self._log.info(
            f"clsCollecteur | Démarrage collecte — "
            f"retry={'actif' if freq_retry_active else 'inactif'}"
        )

        # --- Appel Tesla avec retry éventuel ---
        donnees = self._appeler_tesla_avec_retry(freq_retry_active)

        if donnees is None:
            # Échec définitif — le retry n'a pas abouti
            # Le comptage d'échecs et l'alerte sont gérés dans _appeler_tesla_avec_retry
            return {"succes": False, "erreur": "Véhicule injoignable après toutes les tentatives."}

        # --- Persistance en base ---
        try:
            snp_id = self._persister(donnees)
            self._log.info(f"clsCollecteur | Snapshot enregistré — snp_id={snp_id}")
            self._reinitialiser_compteur_echecs()
            return {"succes": True, "snp_id": snp_id}

        except Exception as e:
            self._log.error(f"clsCollecteur | Erreur persistance : {e}")
            return {"succes": False, "erreur": str(e)}

    # --------------------------------------------------
    # Appel Tesla avec retry
    # --------------------------------------------------

    def _appeler_tesla_avec_retry(self, freq_retry_active: bool) -> dict | None:
        """
        Interroge l'API Tesla.
        Si freq_retry_active → retente N fois à intervalle fixe en cas d'échec.
        Si non → une seule tentative.

        Retourne le dict de données Tesla, ou None si tous les essais ont échoué.
        """
        nb_tentatives = self._params["retry_tentatives"] if freq_retry_active else 1
        delai         = self._params["retry_delai"]

        for essai in range(1, nb_tentatives + 1):

            self._log.info(
                f"clsCollecteur | Tentative {essai}/{nb_tentatives} "
                f"— VIN={self._oVEH.veh_vin}"
            )

            resultat = self._appeler_par_vin()

            if resultat["erreur"] is None:
                return resultat["data"]

            self._log.warning(
                f"clsCollecteur | Tentative {essai} échouée : {resultat['erreur']}"
            )

            if essai < nb_tentatives:
                self._log.info(f"clsCollecteur | Attente {delai}s avant nouvelle tentative.")
                time.sleep(delai)

        # Tous les essais ont échoué
        self._incrementer_compteur_echecs()
        return None

    def _appeler_par_vin(self) -> dict:
        """
        Résout le vehicle_id Tesla depuis le VIN puis appelle get_vehicle_data().
        Encapsule la résolution pour que run() reste lisible.

        Retourne le dict standard {"erreur": ..., "data": ...}.
        """
        res_id = self._vehicle._resolve_vehicle_id(self._oVEH.veh_vin)

        if res_id["erreur"]:
            return res_id

        return self._vehicle.get_vehicle_data(res_id["data"])

    # --------------------------------------------------
    # Persistance SNP + CHG + DRV
    # --------------------------------------------------

    def _persister(self, donnees: dict) -> int:
        """
        Mappe les données Tesla vers SNP, CHG (si branché), DRV (si en conduite),
        puis insère dans db_tstat_data en une transaction unique.

        Retourne le snp_id généré.
        Le commit est effectué ici — cohérent avec la règle :
        commit() au niveau de l'appelant de la couche SQL,
        clsCollecteur est l'orchestrateur de cette transaction.
        """
        # --- Snapshot (SNP) ---
        oSNP = self._mapper_snp(donnees)
        oSNP.insert()
        # snp_id est hydraté par RETURNING après l'insert
        snp_id = oSNP.snp_id

        # --- Données de charge (CHG) — uniquement si branché ---
        charge_state = donnees.get("charge_state", {})
        etat_charge  = charge_state.get("charging_state", "Disconnected")

        if etat_charge in ETATS_BRANCHE:
            oCHG = self._mapper_chg(snp_id, charge_state)
            oCHG.insert()

        # --- Données de conduite (DRV) — uniquement si en mouvement ---
        drive_state    = donnees.get("drive_state", {})
        drv_shiftstate = drive_state.get("shift_state")

        if drv_shiftstate is not None:
            oDRV = self._mapper_drv(snp_id, drive_state)
            oDRV.insert()

        # --- Commit unique — tout ou rien ---
        oSNP.ogEngine.commit()

        return snp_id

    # --------------------------------------------------
    # Mappers Tesla → entités
    # --------------------------------------------------

    def _mapper_snp(self, donnees: dict) -> clsSNP:
        """
        Mappe la réponse Tesla complète vers un objet clsSNP prêt à l'insert.

        snp_timestamp   : converti depuis le timestamp Tesla en millisecondes
        snp_collectedat : horodatage UTC du collecteur (maintenant_utc())
        snp_state       : champ 'state' de la réponse racine Tesla
        snp_odometer    : kilométrage en miles (valeur brute Tesla — conversion à l'affichage)
        snp_firmware    : version firmware depuis vehicle_state.car_version
        """
        # Le timestamp Tesla est en millisecondes depuis epoch UTC
        ts_ms    = donnees.get("vehicle_state", {}).get("timestamp")
        ts_utc   = self._ms_epoch_vers_datetime(ts_ms)

        oSNP = clsSNP()
        oSNP.veh_id         = self._veh_id
        oSNP.snp_timestamp  = ts_utc
        oSNP.snp_collectedat = Tools.maintenant_utc()
        oSNP.snp_state      = donnees.get("state", "unknown")
        oSNP.snp_odometer   = donnees.get("vehicle_state", {}).get("odometer")
        oSNP.snp_firmware   = donnees.get("vehicle_state", {}).get("car_version")

        return oSNP

    def _mapper_chg(self, snp_id: int, charge_state: dict) -> clsCHG:
        """
        Mappe charge_state Tesla vers un objet clsCHG prêt à l'insert.

        Valeurs brutes conservées telles quelles (miles, km/h d'autonomie, etc.)
        La conversion pour l'affichage se fait côté dashboard.
        """
        oCHG = clsCHG()
        oCHG.snp_id           = snp_id
        oCHG.chg_state        = charge_state.get("charging_state")
        oCHG.chg_batterylevel = charge_state.get("battery_level")
        oCHG.chg_usablelevel  = charge_state.get("usable_battery_level")
        oCHG.chg_range        = charge_state.get("battery_range")
        oCHG.chg_limitsoc     = charge_state.get("charge_limit_soc")
        oCHG.chg_power        = charge_state.get("charger_power")
        oCHG.chg_voltage      = charge_state.get("charger_voltage")
        oCHG.chg_current      = charge_state.get("charger_actual_current")
        oCHG.chg_rate         = charge_state.get("charge_rate")
        oCHG.chg_energyadded  = charge_state.get("charge_energy_added")
        oCHG.chg_minutestofull = charge_state.get("minutes_to_full_charge")
        oCHG.chg_fastcharger  = charge_state.get("fast_charger_present", False)
        oCHG.chg_cabletype    = charge_state.get("conn_charge_cable")

        return oCHG

    def _mapper_drv(self, snp_id: int, drive_state: dict) -> clsDRV:
        """
        Mappe drive_state Tesla vers un objet clsDRV prêt à l'insert.
        Appelé uniquement si shift_state est non null.
        """
        oDRV = clsDRV()
        oDRV.snp_id         = snp_id
        oDRV.drv_power      = drive_state.get("power")
        oDRV.drv_shiftstate = drive_state.get("shift_state")
        oDRV.drv_speed      = drive_state.get("speed")

        return oDRV

    # --------------------------------------------------
    # Conversion timestamp Tesla
    # --------------------------------------------------

    @staticmethod
    def _ms_epoch_vers_datetime(ts_ms: int | None) -> datetime | None:
        """
        Convertit un timestamp Tesla en millisecondes (epoch UTC) en datetime UTC.
        Retourne None si ts_ms est None ou invalide.

        Exemple : 1774043474737 → datetime(2026, 3, 20, 21, 51, 14, tzinfo=UTC)
        """
        if ts_ms is None:
            return None
        try:
            return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None

    # --------------------------------------------------
    # Gestion des échecs consécutifs
    # --------------------------------------------------

    def _incrementer_compteur_echecs(self):
        """
        Incrémente le compteur d'échecs consécutifs persistent sur disque.
        Si le seuil est atteint → email critique.

        Le compteur est stocké dans un fichier texte simple dans le dossier logs.
        Pas de table DB — on évite d'écrire en base quand la DB pourrait
        elle-même être la source du problème.
        """
        from sysclasses.cste_chemins import get_app_dir

        chemin = get_app_dir() / "logs" / f"echecs_consecutifs_{self._veh_id}.txt"
        chemin.parent.mkdir(parents=True, exist_ok=True)

        try:
            compteur = int(chemin.read_text(encoding="utf-8").strip()) if chemin.exists() else 0
        except (ValueError, OSError):
            compteur = 0

        compteur += 1
        chemin.write_text(str(compteur), encoding="utf-8")

        self._log.warning(
            f"clsCollecteur | Échecs consécutifs : {compteur} / "
            f"{self._params['retry_max_echecs']}"
        )

        if compteur >= self._params["retry_max_echecs"]:
            self._log.critical(
                f"clsCollecteur | {compteur} échecs consécutifs pour "
                f"veh_id={self._veh_id} — véhicule injoignable."
            )
            # clsLOG.critical() envoie automatiquement l'email en PROD

    def _reinitialiser_compteur_echecs(self):
        """Remet le compteur d'échecs à zéro après un succès."""
        from sysclasses.cste_chemins import get_app_dir

        chemin = get_app_dir() / "logs" / f"echecs_consecutifs_{self._veh_id}.txt"
        if chemin.exists():
            chemin.write_text("0", encoding="utf-8")
            self._log.debug(f"clsCollecteur | Compteur d'échecs remis à zéro.")