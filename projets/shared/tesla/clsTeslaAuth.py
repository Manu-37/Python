"""
shared/Tesla/clsTeslaAuth.py

Gestion de l'authentification OAuth2 Tesla et du cycle de vie des tokens.

Responsabilité unique : obtenir et maintenir un access_token valide.
Les appels API véhicule sont dans clsTeslaVehicle (tstat_collecteur).

Dépendances :
    - clsTTK     : lecture/écriture des tokens en base
    - clsLOG     : logging
    - Tools      : utilitaires date/heure (maintenant_utc, dans_n_secondes, est_expire)
    - requests   : appels HTTP vers Tesla
    - webbrowser : ouverture navigateur pour le flux OAuth2

Flux de démarrage :
    1. Charge clsTTK depuis la base (veh_id)
    2. access_token valide          → prêt, rien à faire
    3. access_token expiré          → refresh silencieux
    4. Aucun token (première fois)  → flux OAuth2 complet (navigateur)

Flux OAuth2 :
    - Le navigateur système s'ouvre sur l'URL d'autorisation Tesla
    - Tesla redirige vers https://emmadesp.freeboxos.fr/tstats?code=XXXX
    - L'utilisateur copie l'URL complète depuis la barre du navigateur
      et la colle dans le prompt affiché dans la console/Jupyter
    - On extrait le code de l'URL et on l'échange contre les tokens
    - Les tokens sont chiffrés et sauvegardés dans clsTTK

Renouvellement automatique :
    - get_access_token() vérifie l'expiration à chaque appel
    - Si expiré → _refresh() transparent, nouveau token sauvegardé
    - Le refresh_token Tesla se renouvelle à chaque refresh
      → pas d'expiration en pratique tant que le collecteur tourne régulièrement
"""

import secrets
import hashlib
import base64
import webbrowser
import requests

from urllib.parse import urlencode, urlparse, parse_qs

from db.db_tstat_admin.public.clsTTK import clsTTK
from sysclasses.clsLOG               import clsLOG
from sysclasses.tools                import Tools


# --------------------------------------------------
# Constantes Tesla Fleet API
# --------------------------------------------------

TESLA_AUTH_URL   = "https://auth.tesla.com/oauth2/v3/authorize"
TESLA_TOKEN_URL  = "https://auth.tesla.com/oauth2/v3/token"
# Marge de sécurité : on considère le token expiré 5 minutes avant son échéance réelle
# pour éviter les appels en toute limite d'expiration
MARGE_EXPIRATION = 300   # secondes


# --------------------------------------------------
# Classe principale
# --------------------------------------------------

class clsTeslaAuth:
    """
    Authentification OAuth2 Tesla et gestion du cycle de vie des tokens.

    Usage :
        auth  = clsTeslaAuth(veh_id=1)
        token = auth.get_access_token()   # toujours valide, refresh si nécessaire
    """

    def __init__(self, veh_id: int):
        self._log    = clsLOG()
        self._veh_id = veh_id
        self._oTTK   = None

        self._charger_ttk()
        self._initialiser_session()

    # --------------------------------------------------
    # Chargement de clsTTK
    # --------------------------------------------------

    def _charger_ttk(self):
        """
        Charge la ligne clsTTK correspondant au veh_id.
        Lève ValueError si la configuration est absente en base.
        """
        self._oTTK = clsTTK(veh_id=self._veh_id)

        if not self._oTTK.ttk_clientid:
            raise ValueError(
                f"clsTeslaAuth | Aucune configuration Tesla trouvée "
                f"pour veh_id={self._veh_id}. "
                "Vérifiez la table t_teslatoken_ttk."
            )

        self._log.info(f"clsTeslaAuth | Configuration chargée pour veh_id={self._veh_id}.")

    # --------------------------------------------------
    # Initialisation de session au démarrage
    # --------------------------------------------------

    def _initialiser_session(self):
        """
        Détermine l'état des tokens au démarrage et agit en conséquence.

        Trois cas :
            1. access_token valide          → rien à faire
            2. access_token expiré          → refresh silencieux
            3. Aucun token (première fois)  → flux OAuth2 complet
        """
        if not self._oTTK.ttk_accesstoken:
            self._log.info("clsTeslaAuth | Aucun token en base — lancement du flux OAuth2.")
            self._lancer_oauth()

        elif Tools.est_expire(self._oTTK.ttk_expiresat, marge_secondes=MARGE_EXPIRATION):
            self._log.info("clsTeslaAuth | Token expiré au démarrage — refresh automatique.")
            self._refresh()

        else:
            self._log.info(
                f"clsTeslaAuth | Token valide jusqu'au "
                f"{Tools.date_en_str(self._oTTK.ttk_expiresat, mode='DT')} UTC."
            )

    # --------------------------------------------------
    # Flux OAuth2 complet
    # --------------------------------------------------

    def _lancer_oauth(self):
        """
        Flux OAuth2 Authorization Code + PKCE.

        PKCE (Proof Key for Code Exchange) :
            Mécanisme de sécurité pour les applis publiques (pas de serveur).
            On génère un code_verifier aléatoire, on en calcule le hash (code_challenge),
            on envoie le challenge à Tesla. Tesla vérifie qu'on connaît le verifier
            lors de l'échange du code — prouve qu'on est bien l'appli qui a initié le flux.

        Étapes :
            1. Générer code_verifier + code_challenge (PKCE)
            2. Ouvrir le navigateur sur l'URL Tesla
            3. L'utilisateur autorise et copie l'URL de callback
            4. On extrait le code de l'URL collée
            5. Échanger le code contre les tokens
            6. Sauvegarder dans clsTTK
        """

        # --- 1. PKCE ---
        code_verifier  = secrets.token_urlsafe(64)
        digest         = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

        # --- 2. Construction de l'URL d'autorisation ---
        redirect_uri = self._oTTK.ttk_redirecturi

        params_url = {
            "client_id":             self._oTTK.ttk_clientid,
            "redirect_uri":          redirect_uri,
            "response_type":         "code",
            "scope":                 self._oTTK.ttk_scopes or "openid vehicle_device_data offline_access",
            "state":                 secrets.token_urlsafe(16),
            "code_challenge":        code_challenge,
            "code_challenge_method": "S256",
        }

        url_auth = f"{TESLA_AUTH_URL}?{urlencode(params_url)}"

        # --- 3. Ouverture navigateur ---
        self._log.info("clsTeslaAuth | Ouverture navigateur pour autorisation Tesla...")
        webbrowser.open(url_auth)

        # --- 4. Saisie manuelle de l'URL de callback ---
        # Tesla redirige vers https://emmadesp.freeboxos.fr/tstats?code=XXXX
        # La page affiche une erreur (normal — pas de serveur derrière)
        # mais l'URL dans la barre du navigateur contient le code.
        print("\n" + "="*60)
        print("AUTORISATION TESLA")
        print("="*60)
        print("1. Connectez-vous sur la page Tesla qui vient de s'ouvrir")
        print("2. Autorisez l'accès")
        print("3. La page suivante affichera une erreur — c'est normal")
        print("4. Copiez l'URL COMPLÈTE depuis la barre du navigateur")
        print("="*60)

        url_retour = input("\nCollez l'URL complète ici puis appuyez sur Entrée :\n> ").strip()

        # --- 5. Extraction du code ---
        parsed = urlparse(url_retour)
        params = parse_qs(parsed.query)
        code   = params.get("code", [None])[0]

        if not code:
            raise ValueError(
                "clsTeslaAuth | Code OAuth2 introuvable dans l'URL fournie.\n"
                "Vérifiez que vous avez copié l'URL complète après redirection Tesla."
            )

        self._log.info("clsTeslaAuth | Code OAuth2 extrait — échange contre les tokens.")

        # --- 6. Échange du code contre les tokens ---
        self._echanger_code(code, code_verifier, redirect_uri)

    # --------------------------------------------------
    # Échange du code OAuth2 contre les tokens
    # --------------------------------------------------

    def _echanger_code(self, code: str, code_verifier: str, redirect_uri: str):
        """
        Appel HTTP POST vers Tesla pour obtenir access_token + refresh_token
        en échange du code d'autorisation reçu via le callback.
        """
        payload = {
            "grant_type":    "authorization_code",
            "client_id":     self._oTTK.ttk_clientid,
            "client_secret": self._oTTK.ttk_clientsecret,
            "code":          code,
            "redirect_uri":  redirect_uri,
            "code_verifier": code_verifier,
        }

        reponse = requests.post(TESLA_TOKEN_URL, data=payload, timeout=30)

        if reponse.status_code != 200:
            raise RuntimeError(
                f"clsTeslaAuth | Échange de code échoué "
                f"({reponse.status_code}) : {reponse.text}"
            )

        self._sauvegarder_tokens(reponse.json())

    # --------------------------------------------------
    # Refresh silencieux
    # --------------------------------------------------

    def _refresh(self):
        """
        Renouvelle le access_token via le refresh_token.
        Tesla renvoie également un nouveau refresh_token — on le sauvegarde.
        Si le refresh échoue (refresh_token expiré), on relance le flux OAuth2.
        """
        self._log.info("clsTeslaAuth | Refresh du token en cours...")

        payload = {
            "grant_type":    "refresh_token",
            "client_id":     self._oTTK.ttk_clientid,
            "refresh_token": self._oTTK.ttk_refreshtoken,
        }

        try:
            reponse = requests.post(TESLA_TOKEN_URL, data=payload, timeout=30)

            if reponse.status_code != 200:
                self._log.warning(
                    f"clsTeslaAuth | Refresh échoué ({reponse.status_code}) "
                    "— relancement du flux OAuth2."
                )
                self._lancer_oauth()
                return

            self._sauvegarder_tokens(reponse.json())
            self._log.info("clsTeslaAuth | Token rafraîchi avec succès.")

        except requests.RequestException as e:
            raise RuntimeError(f"clsTeslaAuth | Erreur réseau lors du refresh : {e}")

    # --------------------------------------------------
    # Sauvegarde des tokens dans clsTTK
    # --------------------------------------------------

    def _sauvegarder_tokens(self, tokens: dict):
        """
        Écrit les tokens reçus de Tesla dans clsTTK et commit.

        Champs mis à jour :
            ttk_accesstoken   : nouveau access_token  (chiffré en base)
            ttk_refreshtoken  : nouveau refresh_token (chiffré en base)
            ttk_idtoken       : id_token si présent   (chiffré en base)
            ttk_expiresin     : durée de validité en secondes (typiquement 28800 = 8h)
            ttk_createdat     : timestamp UTC de création du token
            ttk_expiresat     : timestamp UTC d'expiration (createdat + expiresin)
            ttk_lastrefreshat : timestamp UTC du dernier refresh
        """
        maintenant = Tools.maintenant_utc()
        expires_in = tokens.get("expires_in", 28800)
        expires_at = Tools.dans_n_secondes(expires_in, utc=True)

        self._oTTK.ttk_accesstoken   = tokens.get("access_token",  "")
        self._oTTK.ttk_refreshtoken  = tokens.get("refresh_token",  "")
        self._oTTK.ttk_idtoken       = tokens.get("id_token",       "")
        self._oTTK.ttk_expiresin     = expires_in
        self._oTTK.ttk_createdat     = maintenant
        self._oTTK.ttk_expiresat     = expires_at
        self._oTTK.ttk_lastrefreshat = maintenant

        self._oTTK.update()
        self._oTTK.ogEngine.commit()

        self._log.info(
            f"clsTeslaAuth | Tokens sauvegardés — "
            f"expiration : {Tools.date_en_str(expires_at, mode='DT')} UTC."
        )

    # --------------------------------------------------
    # Interface publique
    # --------------------------------------------------

    def get_access_token(self) -> str:
        """
        Retourne un access_token valide.
        Rafraîchit silencieusement si nécessaire.

        C'est la seule méthode que clsTeslaVehicle doit appeler —
        elle n'a pas à se soucier du cycle de vie des tokens.
        """
        if Tools.est_expire(self._oTTK.ttk_expiresat, marge_secondes=MARGE_EXPIRATION):
            self._log.info("clsTeslaAuth | Token expiré — refresh automatique.")
            self._refresh()

        return self._oTTK.ttk_accesstoken

    @property
    def fleet_url(self) -> str:
        """URL de base de l'API Fleet Tesla — lue depuis clsTTK."""
        return self._oTTK.ttk_fleeturl