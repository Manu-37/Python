import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from pathlib import Path
from .clsINICommun import clsINICommun
from .clsLOG import clsLOG
from .clsCrypto import clsCrypto


class clsEmailManager:
    """
    Gestionnaire des profils d'envoi d'email.
    Singleton : une seule instance par processus, initialisée au démarrage.

    Chaque profil correspond à une section [EMAIL_XXX] dans le .ini.

    Destinataires :
        - Si au moins une liste (destinataires, cc, cci) est fournie à envoyer(),
          elle prend le dessus — aucune liste du .ini n'est utilisée.
        - Si aucune liste n'est fournie, on utilise les destinataires par défaut du profil.
        - Un profil sans recipient dans le .ini est valide — l'appelant devra
          toujours fournir au moins une liste.

    Pièces jointes :
        - Liste de chemins complets.
        - Une PJ introuvable est loggée et mentionnée en fin de corps.
        - Les PJ valides sont attachées, l'email part dans tous les cas.

    Usage :
        clsEmailManager().envoyer(profil="ALERTES", sujet="...", corps="...")
        clsEmailManager().envoyer(profil="ALERTES", sujet="...", corps="...",
                                   destinataires=["a@x.com"], cc=["b@x.com"],
                                   pieces_jointes=["C:/logs/backup.log"])
    """

    _instance = None

    # --------------------------------------------------
    # Singleton via __new__
    # --------------------------------------------------
    def __new__(cls, config_inst=None):
        if cls._instance is None:
            if config_inst is None:
                raise RuntimeError(
                    "clsEmailManager doit être initialisé avec un config_inst au premier appel."
                )
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    def __init__(self, config_inst=None):
        if self._initialized:
            return
        self._initialized = True

        self._log      = clsLOG()
        self._crypto   = clsCrypto()
        self._profiles = {}

        self._charger_profiles(config_inst)

    # --------------------------------------------------
    # Chargement des profils depuis le .ini
    # --------------------------------------------------
    def _charger_profiles(self, config_inst: clsINICommun):
        """
        Lit tous les profils [EMAIL_*] du .ini et déchiffre le mot de passe.
        Le recipient est optionnel — son absence n'invalide pas le profil.
        Un profil mal formé est loggué et ignoré, les autres restent utilisables.
        """
        profiles_bruts = config_inst.email_profiles

        if not profiles_bruts:
            self._log.warning("clsEmailManager | Aucun profil [EMAIL_*] trouvé dans le .ini.")
            return

        for nom, params in profiles_bruts.items():
            try:
                # Clés strictement obligatoires
                for cle in ('smtp_server', 'smtp_port', 'sender', 'password'):
                    if cle not in params:
                        raise KeyError(f"Clé manquante : '{cle}'")

                # Déchiffrement du mot de passe
                pwd_dechiffre = self._crypto.decrypt(params['password'].encode('utf-8'))

                # Destinataires par défaut — optionnels
                recipients_defaut = []
                if 'recipient' in params and params['recipient'].strip():
                    recipients_str    = params['recipient'].replace(';', ',')
                    recipients_defaut = [r.strip() for r in recipients_str.split(',') if r.strip()]

                self._profiles[nom] = {
                    'smtp_server':       params['smtp_server'],
                    'smtp_port':         params['smtp_port'],
                    'sender':            params['sender'],
                    'password':          pwd_dechiffre,
                    'recipients_defaut': recipients_defaut
                }

                mention_dest = (f"{len(recipients_defaut)} destinataire(s) par défaut"
                                if recipients_defaut else "sans destinataires par défaut")
                self._log.info(f"clsEmailManager | Profil '{nom}' chargé — {mention_dest}.")

            except Exception as e:
                self._log.error(f"clsEmailManager | Profil '{nom}' ignoré — {e}")

    # --------------------------------------------------
    # Envoi
    # --------------------------------------------------
    def envoyer(self, profil: str, sujet: str, corps: str,
                destinataires: list = None,
                cc: list            = None,
                cci: list           = None,
                corps_html: str     = None,
                pieces_jointes: list = None) -> bool:
        """
        Envoie un email via le profil indiqué.

        Paramètres :
            profil         : nom du profil (ex: "ALERTES")
            sujet          : sujet de l'email
            corps          : corps texte brut (toujours fourni)
            destinataires  : liste To  — optionnelle
            cc             : liste CC  — optionnelle
            cci            : liste BCC — optionnelle
            corps_html     : corps HTML — optionnel
            pieces_jointes : liste de chemins complets — optionnelle

        Règle destinataires :
            Si au moins une liste est fournie → aucune liste du .ini n'est utilisée.
            Si aucune liste n'est fournie     → destinataires par défaut du profil.

        Retourne True si l'envoi a réussi, False sinon.
        """
        profil = profil.upper()

        if profil not in self._profiles:
            self._log.error(f"clsEmailManager | Profil '{profil}' introuvable.")
            return False

        p = self._profiles[profil]

        # --- 1. Résolution des destinataires ---
        appel_avec_listes = any([destinataires, cc, cci])

        liste_dest = destinataires if destinataires else ([] if appel_avec_listes else p['recipients_defaut'])
        liste_cc   = cc  if cc  else []
        liste_cci  = cci if cci else []

        if not any([liste_dest, liste_cc, liste_cci]):
            self._log.error(
                f"clsEmailManager | Profil '{profil}' — aucun destinataire. "
                "Fournissez une liste ou ajoutez 'recipient' dans le .ini."
            )
            return False

        try:
            # --- 2. Construction du message ---
            msg = MIMEMultipart('mixed')
            msg['Subject'] = sujet
            msg['From']    = p['sender']
            msg['Date'] = formatdate(localtime=True)

            if liste_dest:
                msg['To'] = ', '.join(liste_dest)
            if liste_cc:
                msg['Cc'] = ', '.join(liste_cc)
            # BCC : jamais dans les headers — passé uniquement à sendmail()

            # --- 3. Traitement des pièces jointes ---
            pj_manquantes = []

            if pieces_jointes:
                for chemin_pj in pieces_jointes:
                    chemin = Path(chemin_pj)
                    if not chemin.is_file():
                        self._log.warning(f"clsEmailManager | Pièce jointe introuvable : {chemin_pj}")
                        pj_manquantes.append(chemin.name)
                    else:
                        with open(chemin, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{chemin.name}"')
                        msg.attach(part)

            # --- 4. Enrichissement du corps si PJ manquantes ---
            if pj_manquantes:
                mention  = "\n\n---\nATTENTION - Les pièces jointes suivantes ont été proposées "
                mention += "mais une erreur a empêché leur envoi :\n"
                mention += "\n".join(f"  * {nom}" for nom in pj_manquantes)
                corps += mention

            # --- 5. Construction du corps texte/HTML ---
            corps_part = MIMEMultipart('alternative')
            corps_part.attach(MIMEText(corps, 'plain', 'utf-8'))
            if corps_html:
                corps_part.attach(MIMEText(corps_html, 'html', 'utf-8'))
            msg.attach(corps_part)

            # --- 6. Envoi SMTP ---
            # sendmail reçoit TOUS les destinataires (To + Cc + Bcc)
            # Le Bcc n'apparaît pas dans les headers mais est bien acheminé
            tous_destinataires = liste_dest + liste_cc + liste_cci

            with smtplib.SMTP(p['smtp_server'], p['smtp_port']) as serveur:
                serveur.ehlo()
                serveur.starttls()
                serveur.login(p['sender'], p['password'])
                serveur.sendmail(p['sender'], tous_destinataires, msg.as_string())

            self._log.info(
                f"clsEmailManager | Email '{sujet}' envoyé via profil '{profil}' "
                f"— {len(tous_destinataires)} destinataire(s)."
            )
            return True

        except Exception as e:
            self._log.error(f"clsEmailManager | Échec envoi profil '{profil}' — {e}")
            return False