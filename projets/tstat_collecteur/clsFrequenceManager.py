"""
clsFrequenceManager.py

Decide si le collecteur doit interroger l'API Tesla lors de cette execution.

Responsabilite unique : repondre a la question "est-ce le moment d'appeler Tesla ?".
Aucun appel API, aucune ecriture en base - uniquement de la lecture et de la logique.

Principe de fonctionnement :
    Le cron lance tstat_collecteur.py toutes les 5 minutes.
    clsFrequenceManager consulte le dernier snapshot connu en base
    et compare l'ecart depuis le dernier appel a la frequence cible
    pour l'etat actif du vehicule (charge ou conduite).

    Si l'ecart est insuffisant -> on ne rappelle pas Tesla.
    Si l'ecart est suffisant   -> on rappelle Tesla.

    Quand le vehicule dort (asleep / offline), il ne repond pas -
    le collecteur ne le reveille jamais. La gestion de frequence
    differenciee (nuit, gare long) n'a donc pas d'utilite pratique :
    Tesla gere lui-meme son endormissement.
    On conserve deux frequences distinctes (charge / conduite)
    pour permettre des ajustements fins via le fichier ini.

Etats reconnus :
    "charge"   : vehicule branche (chg_state present et != Disconnected)
                 -> freq_charge (jamais soumis a la plage nocturne :
                    risque de rater la transition Complete/Stopped)
    "conduite" : tout le reste (en mouvement, gare, nuit)
                 -> freq_conduite
                 Le vehicule s'endort de lui-meme si inactif.
    "inconnu"  : aucun snapshot en base -> interrogation immediate

OBSOLETE - code conserve pour retour arriere eventuel.
La logique differenciee (nuit, gare_recent, gare_inactif) a ete abandonnee
au profit d'une logique binaire charge/conduite.
Pour restaurer : decommenter les blocs marques OBSOLETE.
"""

from datetime import datetime, timezone, time as dt_time
from sysclasses.clsLOG import clsLOG


class clsFrequenceManager:
    """
    Gestionnaire de frequence variable pour tstat_collecteur.

    Usage :
        fm = clsFrequenceManager(params=oIni.collecteur_params, veh_id=1)
        if fm.doit_interroger():
            # appeler Tesla
    """

    # Noms des etats actifs
    ETAT_CHARGE   = "charge"
    ETAT_CONDUITE = "conduite"
    ETAT_INCONNU  = "inconnu"

    # OBSOLETE - etats differencies conserves pour retour arriere
    # ETAT_GARE_RECENT   = "gare_recent"
    # ETAT_GARE_INACTIF  = "gare_inactif"
    # ETAT_NUIT          = "nuit"

    def __init__(self, params: dict, veh_id: int):
        self._log    = clsLOG()
        self._params = params
        self._veh_id = veh_id

        # Dernier snapshot charge une seule fois a l'instanciation
        self._dernier_snp = self._charger_dernier_snapshot()

    # --------------------------------------------------
    # Chargement du dernier snapshot
    # --------------------------------------------------

    def _charger_dernier_snapshot(self) -> dict | None:
        """
        Charge le dernier snapshot connu pour ce vehicule depuis db_tstat_data.
        Retourne None si aucun snapshot en base.
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
                f"clsFrequenceManager | Dernier snapshot charge : "
                f"snp_id={res[0]['snp_id']} - etat={res[0]['snp_state']}"
            )
            return res[0]

        self._log.warning(
            f"clsFrequenceManager | Aucun snapshot en base pour veh_id={self._veh_id} "
            "- base vide ou premiere execution. Interrogation immediate."
        )
        return None

    # --------------------------------------------------
    # Determination de l'etat courant
    # --------------------------------------------------

    def _determiner_etat(self) -> str:
        """
        Determine l'etat actif du vehicule depuis le dernier snapshot.

        Priorites :
            1. Aucun snapshot -> inconnu (interrogation immediate)
            2. En charge      -> charge  (jamais soumis a la nuit)
            3. Tout le reste  -> conduite

        OBSOLETE - ancienne logique differenciee (6 etats) :
            1. Plage nocturne ET vehicule non branche -> nuit
            2. Aucun snapshot -> inconnu
            3. En charge -> charge
            4. En conduite -> conduite
            5. Gare depuis < seuil_inactif -> gare_recent
            6. Gare depuis >= seuil_inactif -> gare_inactif

        Code restaurable :
            if self._dernier_snp is None:
                return self.ETAT_INCONNU
            chg_state = self._dernier_snp.get("chg_state")
            if chg_state and chg_state not in ("Disconnected", None):
                return self.ETAT_CHARGE
            if self._est_nuit():
                return self.ETAT_NUIT
            drv_shiftstate = self._dernier_snp.get("drv_shiftstate")
            if drv_shiftstate is not None:
                return self.ETAT_CONDUITE
            ecart = self._ecart_depuis_dernier_snapshot()
            seuil_inactif = self._params["seuil_inactif"]
            if ecart is None or ecart < seuil_inactif:
                return self.ETAT_GARE_RECENT
            return self.ETAT_GARE_INACTIF
        """

        # Priorite 1 : aucun snapshot
        if self._dernier_snp is None:
            return self.ETAT_INCONNU

        # Priorite 2 : en charge - jamais soumis a la plage nocturne
        chg_state = self._dernier_snp.get("chg_state")
        if chg_state and chg_state not in ("Disconnected", None):
            return self.ETAT_CHARGE

        # Priorite 3 : tout le reste
        # Le vehicule s'endort de lui-meme quand il n'a rien a faire.
        return self.ETAT_CONDUITE

    # --------------------------------------------------
    # OBSOLETE - methodes de la logique differenciee
    # --------------------------------------------------

    # def _est_nuit(self) -> bool:
    #     maintenant = datetime.now().time()
    #     debut = self._parse_heure(self._params["nuit_debut"])
    #     fin   = self._parse_heure(self._params["nuit_fin"])
    #     if debut <= fin:
    #         return debut <= maintenant <= fin
    #     else:
    #         return maintenant >= debut or maintenant <= fin
    #
    # @staticmethod
    # def _parse_heure(heure_str: str) -> dt_time:
    #     h, m = heure_str.split(":")
    #     return dt_time(int(h), int(m))

    # --------------------------------------------------
    # Ecart depuis le dernier snapshot
    # --------------------------------------------------

    def _ecart_depuis_dernier_snapshot(self) -> int | None:
        """
        Retourne le nombre de secondes ecoulees depuis le dernier snapshot.
        Retourne None si aucun snapshot disponible.
        """
        if self._dernier_snp is None:
            return None

        dernier = self._dernier_snp.get("snp_collectedat")
        if dernier is None:
            return None

        maintenant = datetime.now(timezone.utc)

        if dernier.tzinfo is None:
            from datetime import timezone as tz
            dernier = dernier.replace(tzinfo=tz.utc)

        return int((maintenant - dernier).total_seconds())

    # --------------------------------------------------
    # Frequence cible selon l'etat
    # --------------------------------------------------

    def _freq_cible(self, etat: str) -> int:
        """
        Retourne la frequence cible en secondes pour l'etat donne.

        OBSOLETE - ancienne table de mapping etendue (6 etats) :
            mapping = {
                self.ETAT_CHARGE:       self._params["freq_charge"],
                self.ETAT_CONDUITE:     self._params["freq_conduite"],
                self.ETAT_GARE_RECENT:  self._params["freq_gare_recent"],
                self.ETAT_GARE_INACTIF: self._params["freq_gare_inactif"],
                self.ETAT_NUIT:         self._params["freq_nuit"],
                self.ETAT_INCONNU:      0,
            }
        """
        mapping = {
            self.ETAT_CHARGE:   self._params["freq_charge"],
            self.ETAT_CONDUITE: self._params["freq_conduite"],
            self.ETAT_INCONNU:  0,
        }
        return mapping.get(etat, self._params["freq_conduite"])

    # --------------------------------------------------
    # Interface publique
    # --------------------------------------------------

    def doit_interroger(self) -> bool:
        """
        Retourne True si le collecteur doit interroger Tesla lors de cette execution.
        """
        etat       = self._determiner_etat()
        freq_cible = self._freq_cible(etat)
        ecart      = self._ecart_depuis_dernier_snapshot()

        self._log.info(
            f"clsFrequenceManager | etat={etat} | "
            f"freq_cible={freq_cible}s | "
            f"ecart={ecart}s"
        )

        if etat == self.ETAT_INCONNU or ecart is None:
            self._log.info("clsFrequenceManager | Premier demarrage -> interrogation immediate.")
            return True

        decision = ecart >= freq_cible

        self._log.info(
            f"clsFrequenceManager | decision={'OUI' if decision else 'NON'} "
            f"({'ecart suffisant' if decision else 'trop tot'})"
        )
        self._log.debug(f"ecart={ecart} - freq_cible={freq_cible}"))

        return decision

    @property
    def etat_courant(self) -> str:
        """Retourne l'etat courant du vehicule (pour logging externe)."""
        return self._determiner_etat()

    @property
    def freq_retry_active(self) -> bool:
        """
        Retourne True si la frequence courante justifie l'activation du retry.
        Regle : freq_cible > seuil_retry_secondes.
        """
        etat       = self._determiner_etat()
        freq_cible = self._freq_cible(etat)
        seuil      = self._params["seuil_retry_secondes"]
        return freq_cible > seuil