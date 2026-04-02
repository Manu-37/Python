"""
clsCollecteur.py

Logique principale du collecteur Tesla.

Responsabilité :
    - Vérifier l'état du véhicule SANS le réveiller
    - Collecter les données uniquement si le véhicule est online de lui-même
    - Mapper la réponse vers clsSNP, clsCHG, clsDRV
    - Persister en base dans une transaction unique
    - Déclencher le REFRESH de mv_charge_sessions sur transition Complete/Stopped
    - Gérer les retries si la fréquence le permet
    - Comptabiliser les échecs consécutifs et alerter

Règle absolue — NE JAMAIS RÉVEILLER LE VÉHICULE :
    L'API Tesla distingue trois états :
        "online"  → véhicule actif, modem opérationnel. Appel gratuit, collecte possible.
        "asleep"  → véhicule en veille profonde. Un wake_up() le réveille et
                    consomme du crédit Tesla (quota gratuit : ~10$/mois).
        "offline" → véhicule hors réseau ou modem éteint. Un wake_up() échoue
                    et risque quand même de consommer du crédit.

    La règle est donc sans exception :
        On ne collecte QUE si le véhicule est déjà "online" de lui-même.
        Pour "asleep" et "offline", on sort immédiatement sans rien faire.
        wake_up() ne doit jamais être appelé par le collecteur automatique.

Contrat de résultat :
    run() retourne un dict :
        {"succes": True,  "snp_id": int}       — snapshot enregistré
        {"succes": False, "erreur": "message"}  — véhicule non online ou échec réseau
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

# --------------------------------------------------
# États qui déclenchent le REFRESH de mv_charge_sessions.
# La session est terminée → données stables → on recalcule la vue.
# --------------------------------------------------
ETATS_FIN_SESSION = ("Complete", "Stopped")

# --------------------------------------------------
# Seul état qui autorise la collecte de données
# --------------------------------------------------
ETAT_ONLINE = "online"


class clsCollecteur:
    """
    Collecteur de données Tesla.

    Principe de fonctionnement :
        1. Vérifier l'état du véhicule sans le réveiller (_get_etat_sans_reveil)
        2. Si online → collecter les données complètes
        3. Si asleep ou offline → sortir immédiatement, ne rien faire

    Usage :
        collecteur = clsCollecteur(veh_id=1, params=oIni.collecteur_params)
        resultat   = collecteur.run(freq_retry_active=True)
    """

    def __init__(self, veh_id: int, params: dict):
        """
        Paramètres :
            veh_id : identifiant du véhicule dans db_tstat_data (et db_tstat_admin)
            params : dict issu de clsINICollecteur.collecteur_params
        """
        self._log    = clsLOG()
        self._veh_id = veh_id
        self._params = params

        # Chargement du véhicule depuis db_tstat_data — référence FK pour les snapshots
        self._oVEH = clsVEH_Data(veh_id=veh_id)

        if not self._oVEH.veh_vin:
            raise ValueError(
                f"clsCollecteur | Véhicule veh_id={veh_id} introuvable "
                "dans db_tstat_data.t_vehicle_veh."
            )

        # Initialisation de l'authentification Tesla
        self._auth    = clsTeslaAuth(veh_id=veh_id)
        self._vehicle = clsTeslaVehicle(self._auth)

        self._log.debug(
            f"clsCollecteur | Initialisé pour {self._oVEH.veh_displayname} "
            f"(VIN={self._oVEH.veh_vin})"
        )

    # --------------------------------------------------
    # Point d'entrée principal
    # --------------------------------------------------

    def run(self, freq_retry_active: bool = False) -> dict:
        """
        Exécute un cycle de collecte complet.

        Retourne :
            {"succes": True,  "snp_id": int}
            {"succes": False, "erreur": "message"}
        """
        donnees = self._appeler_tesla_avec_retry(freq_retry_active)

        if donnees is None:
            return {"succes": False, "erreur": "Véhicule non online ou injoignable."} 

        try:
            snp_id = self._persister(donnees)
            self._log.debug(f"clsCollecteur | Snapshot enregistré — snp_id={snp_id}")
            self._reinitialiser_compteur_echecs()
            return {"succes": True, "snp_id": snp_id}

        except Exception as e:
            self._log.error(f"clsCollecteur | Erreur persistance : {e}")
            return {"succes": False, "erreur": str(e)}

    # --------------------------------------------------
    # Vérification état + collecte sans réveil
    # --------------------------------------------------

    def _appeler_tesla_avec_retry(self, freq_retry_active: bool) -> dict | None:
        """
        Vérifie l'état du véhicule puis collecte ses données si online.

        Règle absolue — NE JAMAIS RÉVEILLER :
            Étape 1 : vérifier l'état via un endpoint léger qui ne réveille pas.
            Étape 2 : si online seulement → collecter les données complètes.
                      si asleep ou offline → sortir immédiatement, rien faire.

        Retourne :
            dict  : données Tesla complètes si collecte réussie
            None  : véhicule non online OU échec réseau après tous les essais
        """
        nb_tentatives = self._params["retry_tentatives"] if freq_retry_active else 1
        delai         = self._params["retry_delai"]

        # --- Étape 1 : vérifier l'état SANS réveiller ---
        etat = self._get_etat_sans_reveil()

        if etat is None:
            self._log.warning(
                "clsCollecteur | Impossible de vérifier l'état du véhicule — "
                "API injoignable. Collecte annulée."
            )
            self._incrementer_compteur_echecs()
            return None

        if etat != ETAT_ONLINE:
            self._log.debug(
                f"clsCollecteur | Véhicule '{etat}' — "
                "pas de collecte, pas de réveil. Comportement normal."
            )
            return None

        # --- Étape 2 : véhicule online → collecter les données complètes ---
        self._log.info(
            f"clsCollecteur | Véhicule online — démarrage collecte "
            f"(retry={'actif' if freq_retry_active else 'inactif'})."
        )

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
                self._log.info(
                    f"clsCollecteur | Attente {delai}s avant nouvelle tentative."
                )
                time.sleep(delai)

        self._log.error(
            f"clsCollecteur | Échec après {nb_tentatives} tentative(s) "
            "— véhicule online mais données inaccessibles."
        )
        self._incrementer_compteur_echecs()
        return None

    def _get_etat_sans_reveil(self) -> str | None:
        """
        Retourne l'état du véhicule SANS le réveiller.

        Utilise l'endpoint sommaire GET /api/1/vehicles/{id} qui retourne
        uniquement les métadonnées du véhicule (id, vin, state...).
        Cet endpoint interroge le serveur Tesla, pas le véhicule directement —
        il ne provoque donc aucun réveil, aucun coût.

        Retourne :
            "online"  : véhicule actif, collecte possible
            "asleep"  : véhicule en veille — NE PAS RÉVEILLER
            "offline" : véhicule hors réseau — NE PAS RÉVEILLER
            None      : échec de l'appel API (réseau, token invalide...)
        """
        res_id = self._vehicle._resolve_vehicle_id(self._oVEH.veh_vin)

        if res_id["erreur"]:
            self._log.warning(
                f"clsCollecteur | _get_etat_sans_reveil — "
                f"impossible de résoudre le vehicle_id : {res_id['erreur']}"
            )
            return None

        etat = self._vehicle._get_vehicle_state(res_id["data"])

        if etat["erreur"]:
            self._log.warning(
                f"clsCollecteur | _get_etat_sans_reveil — "
                f"échec endpoint état : {etat['erreur']}"
            )
            return None

        state = etat["data"].get("state", "unknown")
        self._log.debug(f"clsCollecteur | État véhicule (sans réveil) : '{state}'")
        return state

    def _appeler_par_vin(self) -> dict:
        """
        Appelle get_vehicle_data() avec le vehicle_id Tesla résolu depuis le VIN.
        Appelé UNIQUEMENT si le véhicule est déjà online.
        """
        res_id = self._vehicle._resolve_vehicle_id(self._oVEH.veh_vin)

        if res_id["erreur"]:
            return res_id

        return self._vehicle.get_vehicle_data(res_id["data"])

    # --------------------------------------------------
    # Persistance SNP + CHG + DRV + REFRESH vue
    # --------------------------------------------------

    def _persister(self, donnees: dict) -> int:
        """
        Mappe les données Tesla vers SNP, CHG (si branché), DRV (si en conduite),
        puis insère dans db_tstat_data en une transaction unique.

        Après le commit, si l'état de charge indique une fin de session
        (Complete ou Stopped), déclenche le REFRESH MATERIALIZED VIEW CONCURRENTLY
        de mv_charge_sessions.

        Le REFRESH est exécuté APRÈS le commit car :
            - PostgreSQL interdit REFRESH dans une transaction avec d'autres DML.
            - Les données insérées doivent être visibles avant le recalcul.
            - CONCURRENTLY évite de locker la vue — le dashboard reste lisible.

        Retourne le snp_id généré.
        """
        charge_state = donnees.get("charge_state", {})
        etat_charge  = charge_state.get("charging_state", "Disconnected")

        # --- Snapshot (SNP) ---
        oSNP = self._mapper_snp(donnees)
        oSNP.insert()
        snp_id = oSNP.snp_id

        # --- Données de charge (CHG) — uniquement si branché ---
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

        # --- REFRESH vue matérialisée si fin de session de charge ---
        # Exécuté APRÈS le commit — hors transaction DML.
        # CONCURRENTLY : pas de lock exclusif, dashboard lisible pendant le refresh.
        if etat_charge in ETATS_FIN_SESSION:
            self._refresh_vue_sessions(oSNP.ogEngine)

        return snp_id

    def _refresh_vue_sessions(self, engine):
            """
            Déclenche le REFRESH des deux MV de charge via fct_refresh_all_charge_mv().

            Codes retour PostgreSQL :
                'OK'       — mv_charge_sessions + mv_charge_sessions_ext rafraîchies
                'ERR_MV1'  — échec sur mv_charge_sessions (mv_charge_sessions_ext non tentée)
                'ERR_MV2'  — mv_charge_sessions OK, échec sur mv_charge_sessions_ext

            En cas d'échec partiel ou total, on logue un warning sans interrompre
            le collecteur — le snapshot est déjà committé, les MV seront
            rafraîchies au prochain cycle Complete/Stopped.
            """
            self._log.info("clsCollecteur | Déclenchement REFRESH mv_charge_sessions + mv_charge_sessions_ext.")
            try:
                res = engine.execute_select(
                    "SELECT public.fct_refresh_all_charge_mv() AS statut;"
                )
                statut = res[0]["statut"] if res else "UNKNOWN"

                if statut == "OK":
                    self._log.info(
                        "clsCollecteur | mv_charge_sessions + mv_charge_sessions_ext "
                        "rafraîchies (transition fin de session détectée)."
                    )
                elif statut == "ERR_MV1":
                    self._log.warning(
                        "clsCollecteur | Échec REFRESH mv_charge_sessions — "
                        "mv_charge_sessions_ext non tentée. "
                        "Sera rafraîchie au prochain cycle Complete/Stopped."
                    )
                elif statut == "ERR_MV2":
                    self._log.warning(
                        "clsCollecteur | mv_charge_sessions OK — "
                        "Échec REFRESH mv_charge_sessions_ext. "
                        "Sera rafraîchie au prochain cycle Complete/Stopped."
                    )
                else:
                    self._log.warning(
                        f"clsCollecteur | Statut REFRESH inattendu : '{statut}' — "
                        "vérifier fct_refresh_all_charge_mv()."
                    )

                engine.commit()

            except Exception as e:
                self._log.warning(
                    f"clsCollecteur | Échec appel fct_refresh_all_charge_mv() : {e} — "
                    "MV sera rafraîchie au prochain cycle Complete/Stopped."
                )
    # --------------------------------------------------
    # Mappers Tesla → entités
    # --------------------------------------------------

    def _mapper_snp(self, donnees: dict) -> clsSNP:
        """
        Mappe la réponse Tesla complète vers un objet clsSNP prêt à l'insert.

        snp_timestamp   : converti depuis le timestamp Tesla en ms (UTC)
                          Source : charge_state.timestamp
                          Fallback : vehicle_state.timestamp
        snp_collectedat : horodatage UTC du collecteur au moment de la collecte
        snp_state       : état du véhicule ("online" ici — seul état collecté)
        snp_odometer    : kilométrage en miles — valeur brute Tesla
        snp_firmware    : version firmware embarqué (ex: "2026.8")
        """
        ts_ms = (
            donnees.get("charge_state", {}).get("timestamp")
            or donnees.get("vehicle_state", {}).get("timestamp")
        )
        ts_utc = self._ms_epoch_vers_datetime(ts_ms)

        oSNP = clsSNP()
        oSNP.veh_id          = self._veh_id
        oSNP.snp_timestamp   = ts_utc
        oSNP.snp_collectedat = Tools.maintenant_utc()
        oSNP.snp_state       = donnees.get("state", "unknown")
        oSNP.snp_odometer    = donnees.get("vehicle_state", {}).get("odometer")
        oSNP.snp_firmware    = donnees.get("vehicle_state", {}).get("car_version")

        return oSNP

    def _mapper_chg(self, snp_id: int, charge_state: dict) -> clsCHG:
        """
        Mappe charge_state Tesla vers un objet clsCHG prêt à l'insert.

        Toutes les valeurs sont conservées brutes.
        La conversion pour l'affichage se fait côté dashboard.

        chg_energyadded : kWh ajoutés depuis le début de la session.
                          Accumulateur remis à 0 à chaque nouveau branchement —
                          MAX(chg_energyadded) par session = énergie totale.
        chg_batterylevel : % batterie affiché — utilisé par mv_charge_sessions
                           pour calculer la capacité réelle par règle de trois.
        """
        oCHG = clsCHG()
        oCHG.snp_id            = snp_id
        oCHG.chg_state         = charge_state.get("charging_state")
        oCHG.chg_batterylevel  = charge_state.get("battery_level")
        oCHG.chg_usablelevel   = charge_state.get("usable_battery_level")
        oCHG.chg_range         = charge_state.get("battery_range")
        oCHG.chg_limitsoc      = charge_state.get("charge_limit_soc")
        oCHG.chg_power         = charge_state.get("charger_power")
        oCHG.chg_voltage       = charge_state.get("charger_voltage")
        oCHG.chg_current       = charge_state.get("charger_actual_current")
        oCHG.chg_rate          = charge_state.get("charge_rate")
        oCHG.chg_energyadded   = charge_state.get("charge_energy_added")
        oCHG.chg_minutestofull = charge_state.get("minutes_to_full_charge")
        oCHG.chg_fastcharger   = charge_state.get("fast_charger_present", False)
        oCHG.chg_cabletype     = charge_state.get("conn_charge_cable")

        return oCHG

    def _mapper_drv(self, snp_id: int, drive_state: dict) -> clsDRV:
        """
        Mappe drive_state Tesla vers un objet clsDRV prêt à l'insert.
        Appelé uniquement si shift_state est non null (véhicule en mouvement).

        drv_power : puissance instantanée en kW.
                    Valeur négative = récupération d'énergie au freinage.
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
        Incrémente le compteur d'échecs consécutifs persisté sur disque.
        Si le seuil configuré est atteint → log critical → email en PROD.

        Le compteur est un fichier texte simple dans le dossier logs.
        Choix délibéré de ne pas utiliser la base de données :
        si la DB est la source du problème, on ne veut pas en dépendre
        pour signaler l'erreur.

        Note : un véhicule en état "asleep" ou "offline" n'incrémente PAS
        ce compteur — c'est un comportement normal, pas un échec.
        Seuls les échecs réseau ou API sont comptabilisés ici.
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
                f"veh_id={self._veh_id} — API injoignable ou token invalide."
            )

    def _reinitialiser_compteur_echecs(self):
        """Remet le compteur d'échecs à zéro après une collecte réussie."""
        from sysclasses.cste_chemins import get_app_dir

        chemin = get_app_dir() / "logs" / f"echecs_consecutifs_{self._veh_id}.txt"
        if chemin.exists():
            chemin.write_text("0", encoding="utf-8")
            self._log.debug("clsCollecteur | Compteur d'échecs remis à zéro.")