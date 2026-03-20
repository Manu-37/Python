"""
projets/shared/tesla/clsTeslaVehicle.py

Interrogation de l'API Tesla Fleet — données véhicule.

Responsabilité unique : effectuer des appels HTTP vers l'API Tesla.
La gestion des tokens est déléguée intégralement à clsTeslaAuth.

Dépendances :
    - clsTeslaAuth : fournit get_access_token() et fleet_url
    - clsLOG       : logging
    - requests     : appels HTTP

Contrat de retour — toutes les méthodes publiques retournent un dict structuré :
    Succès : {"erreur": None,             "data": {...}}
    Échec  : {"erreur": "message précis", "data": None}

Jamais d'exception non catchée — l'appelant (tstat_collecteur) décide quoi faire.
"""

import json
import time
import requests

from datetime import datetime
from pathlib import Path

from sysclasses.clsLOG import clsLOG
from sysclasses.cste_chemins import get_app_dir


# --------------------------------------------------
# Constantes
# --------------------------------------------------

TIMEOUT_HTTP      = 30    # secondes — timeout de chaque appel HTTP
WAKE_MAX_ESSAIS   = 5     # nombre maximum de tentatives wake_up
WAKE_DELAI        = 10    # secondes entre chaque tentative wake_up
ETAT_EN_LIGNE     = "online"


# --------------------------------------------------
# Classe principale
# --------------------------------------------------

class clsTeslaVehicle:
    """
    Appels à l'API Tesla Fleet pour un véhicule.

    Usage :
        auth    = clsTeslaAuth(veh_id=1)
        vehicle = clsTeslaVehicle(auth)

        resultat = vehicle.get_vehicles()
        if resultat["erreur"]:
            print(resultat["erreur"])
        else:
            print(resultat["data"])
    """

    def __init__(self, auth):
        """
        Paramètre :
            auth : instance de clsTeslaAuth — fournit le token et l'URL Fleet
        """
        self._auth = auth
        self._log  = clsLOG()

    # --------------------------------------------------
    # Appel générique
    # --------------------------------------------------

    def _call(self, endpoint: str, method: str = "GET", params: dict = None) -> dict:
        """
        Appel HTTP générique vers l'API Tesla Fleet.

        Construit l'URL complète, pose le header Authorization,
        exécute la requête et retourne le dict structuré standard.

        Paramètres :
            endpoint : chemin relatif, ex: "api/1/vehicles"
            method   : "GET" ou "POST"
            params   : dict passé en query string (GET) ou en JSON body (POST)

        Retourne :
            {"erreur": None,    "data": dict}   — succès HTTP 2xx
            {"erreur": "...",   "data": None}   — erreur HTTP ou réseau
        """
        url = f"{self._auth.fleet_url.rstrip('/')}/{endpoint.lstrip('/')}"

        headers = {
            "Authorization": f"Bearer {self._auth.get_access_token()}",
            "Content-Type":  "application/json",
        }

        try:
            if method.upper() == "POST":
                reponse = requests.post(
                    url,
                    headers=headers,
                    json=params or {},
                    timeout=TIMEOUT_HTTP
                )
            else:
                reponse = requests.get(
                    url,
                    headers=headers,
                    params=params or {},
                    timeout=TIMEOUT_HTTP
                )

            # Tesla renvoie 408 (Request Timeout) quand le véhicule est endormi
            if reponse.status_code == 408:
                return {
                    "erreur": f"Véhicule endormi ou injoignable (HTTP 408) — endpoint : {endpoint}",
                    "data":   None
                }

            if reponse.status_code not in (200, 201):
                return {
                    "erreur": (
                        f"Erreur HTTP {reponse.status_code} "
                        f"sur {endpoint} : {reponse.text[:200]}"
                    ),
                    "data": None
                }

            return {"erreur": None, "data": reponse.json()}

        except requests.Timeout:
            msg = f"Timeout ({TIMEOUT_HTTP}s) sur l'appel {endpoint}."
            self._log.warning(f"clsTeslaVehicle | {msg}")
            return {"erreur": msg, "data": None}

        except requests.RequestException as e:
            msg = f"Erreur réseau sur {endpoint} : {e}"
            self._log.error(f"clsTeslaVehicle | {msg}")
            return {"erreur": msg, "data": None}

    # --------------------------------------------------
    # Liste des véhicules du compte
    # --------------------------------------------------

    def get_vehicles(self) -> dict:
        """
        Retourne la liste des véhicules associés au compte Tesla.

        Endpoint : GET /api/1/vehicles

        Retourne :
            {"erreur": None,  "data": [{"id": ..., "vin": ..., ...}, ...]}
            {"erreur": "...", "data": None}
        """
        self._log.debug("clsTeslaVehicle | get_vehicles()")

        resultat = self._call("api/1/vehicles")

        if resultat["erreur"]:
            self._log.error(f"clsTeslaVehicle | get_vehicles échoué : {resultat['erreur']}")
            return resultat

        vehicules = resultat["data"].get("response", [])
        return {"erreur": None, "data": vehicules}

    # --------------------------------------------------
    # Résolution vehicle_id Tesla par VIN (usage interne)
    # --------------------------------------------------

    def _resolve_vehicle_id(self, vin: str) -> dict:
        """
        Retrouve le vehicle_id Tesla correspondant au VIN fourni.

        Appelle get_vehicles() et filtre par VIN.
        Méthode interne — réutilisée par save_snapshot() et potentiellement
        par d'autres méthodes futures nécessitant l'ID Tesla natif.

        Retourne :
            {"erreur": None,  "data": <vehicle_id_tesla: int>}
            {"erreur": "...", "data": None}
        """
        resultat = self.get_vehicles()

        if resultat["erreur"]:
            return resultat

        for v in resultat["data"]:
            if v.get("vin") == vin:
                return {"erreur": None, "data": v.get("id")}

        return {
            "erreur": (
                f"Véhicule VIN={vin} introuvable dans le compte Tesla. "
                "Vérifiez que le VIN correspond bien au compte authentifié."
            ),
            "data": None
        }

    # --------------------------------------------------
    # Réveil du véhicule
    # --------------------------------------------------

    def wake_up(self, vehicle_id: int) -> dict:
        """
        Réveille le véhicule et attend confirmation de mise en ligne.

        Retourne :
            {"erreur": None,  "data": {"state": "online", ...}}
            {"erreur": "...", "data": None}
        """
        self._log.info(f"clsTeslaVehicle | wake_up — vehicle_id={vehicle_id}")

        resultat = self._call(f"api/1/vehicles/{vehicle_id}/wake_up", method="POST")

        if resultat["erreur"]:
            self._log.error(f"clsTeslaVehicle | wake_up POST échoué : {resultat['erreur']}")
            return resultat

        for essai in range(1, WAKE_MAX_ESSAIS + 1):

            etat = self._get_vehicle_state(vehicle_id)

            if etat["erreur"]:
                self._log.warning(
                    f"clsTeslaVehicle | wake_up essai {essai}/{WAKE_MAX_ESSAIS} "
                    f"— erreur état : {etat['erreur']}"
                )
            elif etat["data"].get("state") == ETAT_EN_LIGNE:
                self._log.info(
                    f"clsTeslaVehicle | Véhicule en ligne après {essai} essai(s)."
                )
                return {"erreur": None, "data": etat["data"]}
            else:
                self._log.debug(
                    f"clsTeslaVehicle | wake_up essai {essai}/{WAKE_MAX_ESSAIS} "
                    f"— état : {etat['data'].get('state', 'inconnu')}"
                )

            if essai < WAKE_MAX_ESSAIS:
                time.sleep(WAKE_DELAI)

        msg = (
            f"Véhicule {vehicle_id} non disponible après "
            f"{WAKE_MAX_ESSAIS} tentatives ({WAKE_MAX_ESSAIS * WAKE_DELAI}s)."
        )
        self._log.error(f"clsTeslaVehicle | wake_up — {msg}")
        return {"erreur": msg, "data": None}

    # --------------------------------------------------
    # État sommaire du véhicule (interne — pour wake_up)
    # --------------------------------------------------

    def _get_vehicle_state(self, vehicle_id: int) -> dict:
        """
        Récupère l'état sommaire du véhicule (online / asleep / offline).
        Utilisé en interne par wake_up().

        Retourne :
            {"erreur": None,  "data": {"id": ..., "state": "online", ...}}
            {"erreur": "...", "data": None}
        """
        resultat = self._call(f"api/1/vehicles/{vehicle_id}")

        if resultat["erreur"]:
            return resultat

        return {"erreur": None, "data": resultat["data"].get("response", {})}

    # --------------------------------------------------
    # Snapshot complet du véhicule
    # --------------------------------------------------

    def get_vehicle_data(self, vehicle_id: int) -> dict:
        """
        Récupère le snapshot complet des données du véhicule.
        Réveille le véhicule si nécessaire.

        Retourne :
            {"erreur": None,  "data": {"charge_state": {...}, ...}}
            {"erreur": "...", "data": None}
        """
        self._log.info(f"clsTeslaVehicle | get_vehicle_data — vehicle_id={vehicle_id}")

        resultat = self._call(f"api/1/vehicles/{vehicle_id}/vehicle_data")

        if resultat["erreur"]:
            self._log.info(
                "clsTeslaVehicle | get_vehicle_data — véhicule injoignable, "
                "tentative de réveil."
            )
            reveil = self.wake_up(vehicle_id)

            if reveil["erreur"]:
                return {
                    "erreur": f"Impossible de récupérer les données : {reveil['erreur']}",
                    "data":   None
                }

            resultat = self._call(f"api/1/vehicles/{vehicle_id}/vehicle_data")

            if resultat["erreur"]:
                return {
                    "erreur": (
                        f"Véhicule réveillé mais données inaccessibles : "
                        f"{resultat['erreur']}"
                    ),
                    "data": None
                }

        return {"erreur": None, "data": resultat["data"].get("response", {})}

    # --------------------------------------------------
    # Snapshot complet + sauvegarde JSON
    # --------------------------------------------------

    def save_snapshot(self, vin: str) -> dict:
        """
        Récupère le snapshot complet du véhicule et le sauvegarde en JSON.

        Résout automatiquement le vehicle_id Tesla depuis le VIN,
        puis appelle get_vehicle_data() et écrit le résultat sur disque.

        Nommage fichier : TeslaData_<VIN>_<AAAAMMJJHHMMSS>.json
        Dossier         : <app_dir>/logs/

        Retourne :
            {"erreur": None,  "chemin": Path(...)}   — succès
            {"erreur": "...", "chemin": None}         — échec à n'importe quelle étape
        """
        # --- Résolution vehicle_id Tesla ---
        res_id = self._resolve_vehicle_id(vin)
        if res_id["erreur"]:
            self._log.error(f"clsTeslaVehicle | save_snapshot — {res_id['erreur']}")
            return {"erreur": res_id["erreur"], "chemin": None}

        vehicle_id_tesla = res_id["data"]
        self._log.info(
            f"clsTeslaVehicle | save_snapshot — VIN={vin} → id_tesla={vehicle_id_tesla}"
        )

        # --- Récupération des données ---
        res_data = self.get_vehicle_data(vehicle_id_tesla)
        if res_data["erreur"]:
            self._log.error(f"clsTeslaVehicle | save_snapshot — {res_data['erreur']}")
            return {"erreur": res_data["erreur"], "chemin": None}

        # --- Sauvegarde JSON ---
        horodatage  = datetime.now().strftime("%Y%m%d%H%M%S")
        nom_fichier = f"TeslaData_{vin}_{horodatage}.json"

        dossier_logs = get_app_dir() / "logs"
        dossier_logs.mkdir(parents=True, exist_ok=True)

        chemin = dossier_logs / nom_fichier

        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(res_data["data"], f, indent=2, ensure_ascii=False, default=str)

        self._log.info(f"clsTeslaVehicle | save_snapshot — fichier créé : {chemin}")
        return {"erreur": None, "chemin": chemin}