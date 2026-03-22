"""
clsFrequenceManager.py

Décide si le collecteur doit interroger l'API Tesla lors de cette exécution.

Responsabilité unique : répondre à la question "est-ce le moment d'appeler Tesla ?".
Aucun appel API, aucune écriture en base — uniquement de la lecture et de la logique.

Principe de fonctionnement :
    Le cron lance tstat_collecteur.py toutes les 5 minutes.
    clsFrequenceManager consulte le dernier snapshot connu en base
    pour déterminer l'état actuel du véhicule, puis compare l'écart
    depuis le dernier appel à la fréquence cible pour cet état.

    Si l'écart est insuffisant → on ne rappelle pas Tesla.
    Si l'écart est suffisant   → on rappelle Tesla.

    Cela permet d'avoir une fréquence variable (5 min, 30 min, 2h)
    avec un cron fixe à 5 min, sans modifier le cron.

États reconnus (depuis le dernier snapshot) :
    "charge"       : véhicule branché (charge_state présent et chg_state != Disconnected)
    "conduite"     : véhicule en mouvement (drive_state présent et drv_shiftstate non null)
    "gare_recent"  : garé depuis moins de seuil_inactif secondes
    "gare_inactif" : garé depuis plus de seuil_inactif secondes
    "nuit"         : heure courante dans la plage nocturne (priorité sur les autres états)
    "inconnu"      : aucun snapshot en base — premier démarrage

Cas "inconnu" :
    Aucun snapshot en base = premier démarrage ou base vide.
    On interroge Tesla immédiatement pour établir un état initial.
"""

from datetime import datetime, timezone, time as dt_time
from sysclasses.clsLOG import clsLOG


class clsFrequenceManager:
    """
    Gestionnaire de fréquence variable pour tstat_collecteur.

    Usage :
        fm = clsFrequenceManager(params=oIni.collecteur_params, veh_id=1)
        if fm.doit_interroger():
            # appeler Tesla
    """

    # Noms des états — constantes pour éviter les fautes de frappe
    ETAT_CHARGE        = "charge"
    ETAT_CONDUITE      = "conduite"
    ETAT_GARE_RECENT   = "gare_recent"
    ETAT_GARE_INACTIF  = "gare_inactif"
    ETAT_NUIT          = "nuit"
    ETAT_INCONNU       = "inconnu"

    def __init__(self, params: dict, veh_id: int):
        """
        Paramètres :
            params : dict issu de clsINICollecteur.collecteur_params
            veh_id : identifiant du véhicule dans db_tstat_data
        """
        self._log    = clsLOG()
        self._params = params
        self._veh_id = veh_id

        # Dernier snapshot chargé une seule fois à l'instanciation
        # Évite de faire plusieurs requêtes pour le même appel
        self._dernier_snp = self._charger_dernier_snapshot()

    # --------------------------------------------------
    # Chargement du dernier snapshot
    # --------------------------------------------------

    def _charger_dernier_snapshot(self) -> dict | None:
        """
        Charge le dernier snapshot connu pour ce véhicule depuis db_tstat_data.
        Retourne un dict avec snp_*, chg_state (si existe), drv_shiftstate (si existe).
        Retourne None si aucun snapshot en base.

        On fait une requête directe plutôt que de passer par clsSNP
        pour éviter N+1 requêtes (SNP puis CHG puis DRV séparément).
        Une seule requête avec LEFT JOIN couvre les trois tables.
        """
        from sysclasses.clsDBAManager import clsDBAManager
        engine = clsDBAManager().get_db("TSTAT_DATA")

        sql = """
            SELECT
                s.snp_id,
                s.snp_timestamp,
                s.snp_collectedat,
                s.snp_state,
                s.snp_odometer,
                c.chg_state,
                d.drv_shiftstate
            FROM public.t_snapshot_snp s
            LEFT JOIN public.t_charge_chg c ON c.snp_id = s.snp_id
            LEFT JOIN public.t_drive_drv  d ON d.snp_id = s.snp_id
            WHERE s.veh_id = %s
            ORDER BY s.snp_timestamp DESC
            LIMIT 1
        """

        res = engine.execute_select(sql, (self._veh_id,))

        if res:
            self._log.debug(
                f"clsFrequenceManager | Dernier snapshot chargé : "
                f"snp_id={res[0]['snp_id']} — état={res[0]['snp_state']}"
            )
            return res[0]

        self._log.warning(
            f"clsFrequenceManager | Aucun snapshot en base pour veh_id={self._veh_id} "
            "— base vide ou première exécution. Interrogation immédiate."
        )
        return None

    # --------------------------------------------------
    # Détermination de l'état courant
    # --------------------------------------------------

    def _determiner_etat(self) -> str:
        """
        Détermine l'état du véhicule depuis le dernier snapshot.

        Priorités :
            1. Plage nocturne — prioritaire sur tout
            2. Aucun snapshot → inconnu
            3. En charge
            4. En conduite
            5. Garé récent / inactif selon l'écart depuis le dernier snapshot
        """

        # --- Priorité 1 : plage nocturne ---
        if self._est_nuit():
            return self.ETAT_NUIT

        # --- Priorité 2 : aucun snapshot ---
        if self._dernier_snp is None:
            return self.ETAT_INCONNU

        # --- Priorité 3 : en charge ---
        chg_state = self._dernier_snp.get("chg_state")
        if chg_state and chg_state not in ("Disconnected", None):
            return self.ETAT_CHARGE

        # --- Priorité 4 : en conduite ---
        drv_shiftstate = self._dernier_snp.get("drv_shiftstate")
        if drv_shiftstate is not None:
            return self.ETAT_CONDUITE

        # --- Priorité 5 : garé récent ou inactif ---
        ecart = self._ecart_depuis_dernier_snapshot()
        seuil_inactif = self._params["seuil_inactif"]

        if ecart is None or ecart < seuil_inactif:
            return self.ETAT_GARE_RECENT

        return self.ETAT_GARE_INACTIF

    # --------------------------------------------------
    # Plage nocturne
    # --------------------------------------------------

    def _est_nuit(self) -> bool:
        """
        Retourne True si l'heure locale courante est dans la plage nocturne.

        Gère le cas où la plage enjambe minuit (ex: 23:00 → 06:00).
        """
        maintenant = datetime.now().time()

        debut = self._parse_heure(self._params["nuit_debut"])
        fin   = self._parse_heure(self._params["nuit_fin"])

        if debut <= fin:
            # Plage dans la même journée (ex: 01:00 → 05:00 — cas rare)
            return debut <= maintenant <= fin
        else:
            # Plage enjambe minuit (ex: 23:00 → 06:00 — cas normal)
            return maintenant >= debut or maintenant <= fin

    @staticmethod
    def _parse_heure(heure_str: str) -> dt_time:
        """Convertit une string 'HH:MM' en objet time."""
        h, m = heure_str.split(":")
        return dt_time(int(h), int(m))

    # --------------------------------------------------
    # Écart depuis le dernier snapshot
    # --------------------------------------------------

    def _ecart_depuis_dernier_snapshot(self) -> int | None:
        """
        Retourne le nombre de secondes écoulées depuis le dernier snapshot.
        Retourne None si aucun snapshot disponible.

        Utilise snp_collectedat (horodatage collecteur UTC) plutôt que
        snp_timestamp (horodatage Tesla) pour mesurer l'écart réel
        entre deux exécutions du collecteur.
        """
        if self._dernier_snp is None:
            return None

        dernier = self._dernier_snp.get("snp_collectedat")
        if dernier is None:
            return None

        maintenant = datetime.now(timezone.utc)

        # snp_collectedat est un TIMESTAMPTZ — psycopg2 le retourne
        # avec tzinfo. On s'assure que la comparaison est cohérente.
        if dernier.tzinfo is None:
            # Sécurité si jamais retourné sans timezone
            from datetime import timezone as tz
            dernier = dernier.replace(tzinfo=tz.utc)

        return int((maintenant - dernier).total_seconds())

    # --------------------------------------------------
    # Fréquence cible selon l'état
    # --------------------------------------------------

    def _freq_cible(self, etat: str) -> int:
        """Retourne la fréquence cible en secondes pour l'état donné."""
        mapping = {
            self.ETAT_CHARGE:       self._params["freq_charge"],
            self.ETAT_CONDUITE:     self._params["freq_charge"],   # même fréquence que charge
            self.ETAT_GARE_RECENT:  self._params["freq_gare_recent"],
            self.ETAT_GARE_INACTIF: self._params["freq_gare_inactif"],
            self.ETAT_NUIT:         self._params["freq_nuit"],
            self.ETAT_INCONNU:      0,   # inconnu → on interroge immédiatement
        }
        return mapping.get(etat, self._params["freq_gare_inactif"])

    # --------------------------------------------------
    # Interface publique
    # --------------------------------------------------

    def doit_interroger(self) -> bool:
        """
        Retourne True si le collecteur doit interroger Tesla lors de cette exécution.

        Logique :
            1. Déterminer l'état du véhicule
            2. Calculer la fréquence cible pour cet état
            3. Comparer l'écart depuis le dernier snapshot à la fréquence cible
            4. Si écart >= fréquence cible (ou état inconnu) → True
        """
        etat       = self._determiner_etat()
        freq_cible = self._freq_cible(etat)
        ecart      = self._ecart_depuis_dernier_snapshot()

        self._log.info(
            f"clsFrequenceManager | état={etat} | "
            f"freq_cible={freq_cible}s | "
            f"ecart={ecart}s"
        )

        # Cas inconnu ou premier démarrage — on interroge toujours
        if etat == self.ETAT_INCONNU or ecart is None:
            self._log.info("clsFrequenceManager | Premier démarrage → interrogation immédiate.")
            return True

        decision = ecart >= freq_cible

        self._log.info(
            f"clsFrequenceManager | décision={'OUI' if decision else 'NON'} "
            f"({'écart suffisant' if decision else 'trop tôt'})"
        )

        return decision

    @property
    def etat_courant(self) -> str:
        """Retourne l'état courant du véhicule (pour logging externe)."""
        return self._determiner_etat()

    @property
    def freq_retry_active(self) -> bool:
        """
        Retourne True si la fréquence courante est suffisamment grande
        pour que le mécanisme de retry ait du sens.

        Règle : freq_cible > seuil_retry_secondes
        En dessous du seuil, le prochain cron arrive avant la fin des retries
        → on n'active pas le retry pour éviter les chevauchements.
        """
        etat       = self._determiner_etat()
        freq_cible = self._freq_cible(etat)
        seuil      = self._params["seuil_retry_secondes"]
        return freq_cible > seuil