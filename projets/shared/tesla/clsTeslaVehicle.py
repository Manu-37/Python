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

import time
import requests

from sysclasses.clsLOG import clsLOG


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
            # et 200 avec response body quand tout va bien
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

        # L'API renvoie {"response": [...], "count": N}
        # On expose directement la liste pour simplifier l'usage
        vehicules = resultat["data"].get("response", [])
        return {"erreur": None, "data": vehicules}

    # --------------------------------------------------
    # Réveil du véhicule
    # --------------------------------------------------

    def wake_up(self, vehicle_id: int) -> dict:
        """
        Réveille le véhicule et attend confirmation de mise en ligne.

        Tesla endort le véhicule après une période d'inactivité pour
        préserver la batterie. Avant tout appel de données, il faut
        s'assurer que le véhicule est "online".

        Stratégie :
            - POST /api/1/vehicles/{id}/wake_up
            - Interroger l'état toutes les WAKE_DELAI secondes
            - Maximum WAKE_MAX_ESSAIS tentatives

        Retourne :
            {"erreur": None,  "data": {"state": "online", ...}}  — véhicule en ligne
            {"erreur": "...", "data": None}                       — échec ou timeout
        """
        self._log.info(f"clsTeslaVehicle | wake_up — vehicle_id={vehicle_id}")

        # Envoi de la commande de réveil
        resultat = self._call(f"api/1/vehicles/{vehicle_id}/wake_up", method="POST")

        if resultat["erreur"]:
            self._log.error(f"clsTeslaVehicle | wake_up POST échoué : {resultat['erreur']}")
            return resultat

        # Attente de la mise en ligne
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

            # Pas encore en ligne — on attend avant le prochain essai,
            # sauf si c'était le dernier
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
        Utilisé en interne par wake_up() pour vérifier la mise en ligne.

        Endpoint : GET /api/1/vehicles/{id}

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

        Endpoint : GET /api/1/vehicles/{id}/vehicle_data

        Le snapshot contient :
            charge_state    : niveau batterie, autonomie, état de charge
            climate_state   : température, climatisation
            drive_state     : position GPS, vitesse, cap
            vehicle_state   : kilométrage, verrouillage, mise à jour SW
            gui_settings    : unités d'affichage

        Retourne :
            {"erreur": None,  "data": {"charge_state": {...}, ...}}
            {"erreur": "...", "data": None}
        """
        self._log.info(f"clsTeslaVehicle | get_vehicle_data — vehicle_id={vehicle_id}")

        # Tentative directe — le véhicule est peut-être déjà en ligne
        resultat = self._call(f"api/1/vehicles/{vehicle_id}/vehicle_data")

        # Si le véhicule est endormi (408 ou erreur explicite), on le réveille
        if resultat["erreur"]:
            self._log.info(
                f"clsTeslaVehicle | get_vehicle_data — véhicule injoignable, "
                "tentative de réveil."
            )
            reveil = self.wake_up(vehicle_id)

            if reveil["erreur"]:
                return {
                    "erreur": f"Impossible de récupérer les données : {reveil['erreur']}",
                    "data":   None
                }

            # Deuxième tentative après réveil
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