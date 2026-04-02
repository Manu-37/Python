import os
import platform
import inspect
import uuid
import time
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from typing import Optional, List, Union

class Tools:
    # Constantes
    kREPDONNEES = 'REPDONNEES'  # Répertoire des données    

    @staticmethod
    def list_file(chemin_d_acces: Union[str, Path], type_fichier: Optional[str] = None, prefixe_fichier: Optional[str] = None, contient_nom: Optional[str] = None) -> List[str]:
        """
        Retourne la liste des fichiers (sans les sous-répertoires) du chemin d'accès,
        éventuellement filtrée par type (extension), préfixe, ou si le nom contient une chaîne.

        Utilise pathlib.Path.
        """
        chemin = Path(chemin_d_acces)

        # 1. Création du répertoire s'il n'existe pas (conforme à l'original)
        if not chemin.exists():
            chemin.mkdir(parents=True)
        
        # 2. Utilisation de glob pour lister et filtrer les fichiers (plus performant que listdir + isfile)
        liste_fichiers = [f for f in chemin.glob('*') if f.is_file()]
        
        fichiers_seuls = [f.name for f in liste_fichiers]

        # Filtre par extension si précisé (ex: type_fichier='.txt')
        if type_fichier != '*' and type_fichier is not None:
            ext = type_fichier if type_fichier.startswith('.') else '.' + type_fichier
            fichiers_seuls = [f for f in fichiers_seuls if f.endswith(ext)]
        
        # Filtre par préfixe si précisé
        if prefixe_fichier:
            fichiers_seuls = [f for f in fichiers_seuls if f.startswith(prefixe_fichier)]
        
        # Filtre "contient" si précisé
        if contient_nom:
            fichiers_seuls = [f for f in fichiers_seuls if contient_nom in f]
        
        return fichiers_seuls
    
    @staticmethod
    def get_current_directory() -> str:
        """
        Retourne le répertoire de travail actuel, toujours terminé par un séparateur.
        (Convention forte de l'utilisateur).
        """
        repertoire_courant = str(Path.cwd())
        
        if repertoire_courant[-1] != os.sep:
            repertoire_courant += os.sep
        return repertoire_courant
    
    @staticmethod
    def get_common_data_dir(app_name: str) -> str:
        """
        Retourne le répertoire commun d'installation des données de l'application
        en fonction du système d'exploitation.
        """
        system = platform.system()
        if system == "Windows":
            base = os.environ.get('PROGRAMDATA', r'C:\ProgramData')
            return os.path.join(base, app_name)
        elif system == "Darwin":
            return f"/Library/Application Support/{app_name}"
        else:
            return f"/var/lib/{app_name}"

    # --- Gestion du Temps et des Dates ---

    @staticmethod
    def date_du_jour() -> date:
        """
        Retourne la date du jour sous forme d'objet date (heure locale).
        Exemple : date(2026, 3, 18)

        Pour obtenir une string : Tools.date_en_str(Tools.date_du_jour(), mode='D')
        """
        return date.today()

    @staticmethod
    def maintenant() -> datetime:
        """
        Retourne la date et l'heure courante locale sous forme d'objet datetime.
        Exemple : datetime(2026, 3, 18, 14, 35, 22, ...)

        Pour obtenir une string : Tools.date_en_str(Tools.maintenant(), mode='DT')
        """
        return datetime.now()

    @staticmethod
    def maintenant_utc() -> datetime:
        """
        Retourne la date et l'heure courante en UTC sous forme d'objet datetime
        avec timezone explicite (tzinfo=UTC).
        Exemple : datetime(2026, 3, 18, 13, 35, 22, tzinfo=timezone.utc)

        À utiliser impérativement pour tout ce qui touche aux tokens Tesla,
        aux timestamps stockés en base en TIMESTAMP WITH TIME ZONE,
        ou à toute comparaison avec des valeurs externes exprimées en UTC.

        Pour obtenir une string : Tools.date_en_str(Tools.maintenant_utc(), mode='DT')
        """
        return datetime.now(timezone.utc)

    @staticmethod
    def dans_n_secondes(n: int, utc: bool = False) -> datetime:
        """
        Retourne un datetime correspondant à maintenant + n secondes.

        utc=False (défaut) : heure locale — pour les calculs applicatifs courants
        utc=True           : UTC         — pour les tokens Tesla et timestamps base

        Exemple :
            Tools.dans_n_secondes(28800)        # dans 8 heures, heure locale
            Tools.dans_n_secondes(28800, utc=True)  # dans 8 heures, UTC
        """
        base = Tools.maintenant_utc() if utc else Tools.maintenant()
        return base + timedelta(seconds=n)

    @staticmethod
    def est_expire(dt: datetime, marge_secondes: int = 0) -> bool:
        """
        Retourne True si le datetime fourni est dépassé.

        Gestion automatique des timezones :
            - Si dt a une timezone (ex: UTC) → comparaison en UTC
            - Si dt n'a pas de timezone      → comparaison en heure locale

        marge_secondes : anticipation optionnelle en secondes.
            Ex: marge_secondes=300 → considère le datetime expiré 5 minutes avant
            son échéance réelle. Utile pour les tokens Tesla (évite les appels
            en toute limite d'expiration).

        Exemple :
            Tools.est_expire(oTTK.ttk_expiresat, marge_secondes=300)
        """
        if dt is None:
            return True

        marge = timedelta(seconds=marge_secondes)

        if dt.tzinfo is not None:
            # datetime avec timezone → comparaison en UTC
            maintenant = Tools.maintenant_utc()
        else:
            # datetime sans timezone → comparaison en local
            maintenant = Tools.maintenant()

        return maintenant >= (dt - marge)

    @staticmethod
    def date_en_str(dt: Union[datetime, date], mode: str = 'DT') -> str:
        """
        Convertit un objet datetime ou date en chaîne formatée.

        mode :
            'D'  → date seule        : "2026-03-18"
            'T'  → heure seule       : "14:35:22"
            'DT' → date et heure     : "2026-03-18 14:35:22"

        Fonctionne avec datetime local, datetime UTC, et date simple.
        Pour 'T' avec un objet date (sans heure), retourne "00:00:00".

        Exemple :
            Tools.date_en_str(Tools.maintenant(), mode='DT')
            Tools.date_en_str(Tools.date_du_jour(), mode='D')
            Tools.date_en_str(Tools.maintenant_utc(), mode='T')
        """
        formats = {
            'D':  '%Y-%m-%d',
            'T':  '%H:%M:%S',
            'DT': '%Y-%m-%d %H:%M:%S',
        }
        fmt = formats.get(mode.upper())
        if fmt is None:
            raise ValueError(
                f"Tools.date_en_str | mode '{mode}' invalide. "
                "Valeurs acceptées : 'D', 'T', 'DT'."
            )

        # Un objet date n'a pas d'attribut strftime pour l'heure
        # On le convertit en datetime minuit pour uniformiser
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime(dt.year, dt.month, dt.day)

        return dt.strftime(fmt)

    @staticmethod
    def str_en_date(date_str: str) -> datetime:
        """
        Convertit une chaîne de caractères au format 'YYYY-MM-DD'
        en un objet datetime (heure locale, minuit).

        Si le format est invalide, retourne la date du jour à minuit
        (convention de l'utilisateur).

        Exemple :
            Tools.str_en_date("2026-03-18")  # datetime(2026, 3, 18, 0, 0, 0)
        """
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return datetime.combine(date.today(), datetime.min.time())

    @staticmethod
    def add_days_to_date(date_date: datetime, days: int) -> datetime:
        """
        Ajoute un nombre de jours à un objet datetime donné.
        """
        return date_date + timedelta(days=days)
        
    @staticmethod
    def get_current_time() -> float:
        """
        Retourne l'heure actuelle au format float (timestamp Unix).
        """
        return time.time()
    
    # --- Gestion des Fichiers ---

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        Retourne la taille du fichier en octets.
        Le fichier fourni en paramètre doit être le path complet du fichier.
        Lève FileNotFoundError si le fichier n'existe pas.
        """
        chemin = Path(file_path)
        if not chemin.is_file():
             raise FileNotFoundError(f"Le fichier '{file_path}' n'existe pas.")
        return chemin.stat().st_size
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]):
        """
        Supprime le fichier spécifié par file_path.
        Lève FileNotFoundError si le fichier n'existe pas.
        """
        chemin = Path(file_path)
        if not chemin.is_file():
            raise FileNotFoundError(f"Le fichier '{file_path}' n'existe pas.")
        chemin.unlink()

    @staticmethod
    def delete_directory(directory_path: Union[str, Path]):
        """
        Supprime le répertoire spécifié par directory_path.
        Lève FileNotFoundError si le répertoire n'existe pas.
        Note: Le répertoire doit être vide. Utiliser shutil.rmtree pour les répertoires non vides.
        """
        chemin = Path(directory_path)
        if not chemin.is_dir():
            raise FileNotFoundError(f"Le répertoire '{directory_path}' n'existe pas.")
        chemin.rmdir()

    @staticmethod
    def cree_fichier_si_inexistant(chemin_fichier: Union[str, Path]):
        """
        Crée un fichier s'il n'existe pas déjà.
        Si le répertoire parent n'existe pas, il est créé.
        """
        chemin = Path(chemin_fichier)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        if not chemin.is_file():
            chemin.touch()

    # --- Informations Système ---

    @staticmethod
    def get_nom_reseau() -> Optional[str]:
        """
        Retourne le nom du réseau de l'ordinateur.
        """
        try:
            return platform.node()
        except Exception:
            return None
        
    @staticmethod 
    def get_separator() -> str:
        """
        Retourne le séparateur de répertoire utilisé par le système d'exploitation.
        """
        return os.sep

    # --- GUIDs (UUIDs) ---

    @staticmethod
    def get_guid() -> str:
        """
        Génère un UUID unique (avec tirets).
        """
        return str(uuid.uuid4())
        
    @staticmethod
    def get_guid_brut() -> str:
        """
        Retourne un GUID brut (UUID) sans tirets.
        """
        return uuid.uuid4().hex
    
    # --- Réflexion et Vérification ---

    @staticmethod
    def get_function_name() -> str: 
        """
        Retourne le nom du fichier, de la classe et de la fonction appelante (niveau -1)
        sous la forme Fichier/Classe/Méthode.
        """
        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            if caller_frame is not None:
                fichier = os.path.basename(caller_frame.f_code.co_filename)
                classe = ""
                if 'self' in caller_frame.f_locals:
                    classe = caller_frame.f_locals['self'].__class__.__name__
                elif 'cls' in caller_frame.f_locals:
                    classe = caller_frame.f_locals['cls'].__name__
                methode = caller_frame.f_code.co_name
                return f"{fichier}/{classe}/{methode}"
        return "UnknownFunction"
    
    @staticmethod
    def get_function_name_2() -> str: 
        """
        Retourne le nom du fichier, de la classe et de la fonction appelante au niveau -2,
        sous la forme Fichier/Classe/Méthode.
        """
        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            if caller_frame is not None:
                caller2_frame = caller_frame.f_back
                if caller2_frame is not None:
                    fichier = os.path.basename(caller2_frame.f_code.co_filename)
                    classe = ""
                    if 'self' in caller2_frame.f_locals:
                        classe = caller2_frame.f_locals['self'].__class__.__name__
                    elif 'cls' in caller2_frame.f_locals:
                        classe = caller2_frame.f_locals['cls'].__name__
                    methode = caller2_frame.f_code.co_name
                    return f"{fichier}/{classe}/{methode}"
        return "UnknownFunction"

    @staticmethod
    def verifier_methode(objet: object, nom_methode: str) -> bool:
        """
        Vérifie si la méthode passée en paramètre existe et est appelable dans l'instance.
        Lève une exception spécifique (AttributeError ou TypeError) si non.
        """
        if not hasattr(objet, nom_methode):
            raise AttributeError(f"La méthode ou attribut '{nom_methode}' n'existe pas sur l'objet de type {type(objet).__name__}.")
        methode = getattr(objet, nom_methode)
        if not callable(methode):
            raise TypeError(f"L'attribut '{nom_methode}' existe, mais n'est pas appelable (n'est pas une méthode ou fonction).")
        return True
        
    @staticmethod
    def methode_existe(objet: object, nom_methode: str) -> bool:
        """
        Vérifie si une méthode existe dans l'objet.
        Ne préjuge pas si la méthode est exécutable.
        """
        return hasattr(objet, nom_methode)

    # --- Conversions ---

    @staticmethod
    def miles_to_km(miles: float, decimales: int = 6) -> float:
        """
        Convertit des miles en kilomètres.
        Facteur : 1 mile = 1.609344 km (définition internationale 1959).

        Paramètres :
            miles     : valeur numérique en miles
            decimales : précision du résultat arrondi (défaut 6).
                        Choisir selon l'usage ultérieur :
                        - 6 si les valeurs sont agrégées après conversion
                          (minimise l'accumulation d'erreurs d'arrondi)
                        - 3 si la valeur est une donnée finale non reagrégée

        Lève TypeError si miles n'est pas numérique.

        Exemple :
            Tools.miles_to_km(63854.221895)     → 102766.942...
            Tools.miles_to_km(63854.221895, 3)  → 102766.943
            Tools.miles_to_km(63854.221895, 0)  → 102767.0
        """
        return round(float(miles) * 1.609344, decimales)

    @staticmethod
    def km_to_miles(km: float, decimales: int = 6) -> float:
        """
        Convertit des kilomètres en miles.
        Facteur : 1 mile = 1.609344 km (définition internationale 1959).

        Paramètres :
            km        : valeur numérique en kilomètres
            decimales : précision du résultat arrondi (défaut 6).
                        Choisir selon l'usage ultérieur :
                        - 6 si les valeurs sont agrégées après conversion
                        - 3 si la valeur est une donnée finale non reagrégée

        Lève TypeError si km n'est pas numérique.

        Exemple :
            Tools.km_to_miles(102766.943)       → 63854.221...
            Tools.km_to_miles(102766.943, 3)    → 63854.221
            Tools.km_to_miles(102766.943, 0)    → 63854.0
        """
        return round(float(km) / 1.609344, decimales)