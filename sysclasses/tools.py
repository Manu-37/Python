import os
import platform
import inspect
import uuid
import time
from datetime import datetime, timedelta
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
        # On utilise une expression générique pour lister tous les fichiers
        liste_fichiers = [f for f in chemin.glob('*') if f.is_file()]
        
        fichiers_seuls = [f.name for f in liste_fichiers]

        # Filtre par extension si précisé (ex: type_fichier='.txt')
        if type_fichier != '*' and type_fichier is not None:
            # Assure que le type_fichier commence par '.' s'il y a une extension
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
        # Utilisation de Path pour un accès moderne au répertoire
        repertoire_courant = str(Path.cwd())
        
        # Application de la convention de terminaison par séparateur
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
            # PROGRAMDATA est la variable standard Windows pour les données communes
            base = os.environ.get('PROGRAMDATA', r'C:\ProgramData')
            return os.path.join(base, app_name)
        elif system == "Darwin":  # macOS
            return f"/Library/Application Support/{app_name}"
        else:  # Linux et autres Unix (utilisation de /var/lib pour les données d'application)
            return f"/var/lib/{app_name}"

    # --- Gestion du Temps et des Dates ---
    
    @staticmethod
    def date_du_jour() -> str:
        """
        Retourne la date du jour au format 'YYYY-MM-DD'.
        """
        return datetime.today().strftime('%Y-%m-%d')
    
    @staticmethod
    def maintenant() -> str:
        """
        Retourne l'heure actuelle au format 'HH:MM:SS'.
        """
        return datetime.now().strftime('%H:%M:%S')
    
    @staticmethod
    def date_en_date(Date_str: str) -> datetime:
        """
        Convertit une chaîne de caractères représentant une date au format 'YYYY-MM-DD'
        en un objet datetime. 
        
        Si le format est invalide, retourne la date du jour (Convention de l'utilisateur).
        """
        try:
            return datetime.strptime(Date_str, '%Y-%m-%d')
        except ValueError:
            # Conserver la date du jour en cas d'erreur selon la convention utilisateur
            return datetime.strptime(Tools.date_du_jour(), '%Y-%m-%d') 

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
        
        return chemin.stat().st_size # Utilisation de stat().st_size de pathlib
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]):
        """
        Supprime le fichier spécifié par file_path.
        Lève FileNotFoundError si le fichier n'existe pas.
        """
        chemin = Path(file_path)
        if not chemin.is_file():
            raise FileNotFoundError(f"Le fichier '{file_path}' n'existe pas.")
        
        chemin.unlink() # Méthode de suppression de pathlib

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
        
        chemin.rmdir() # Méthode de suppression de répertoire de pathlib

    @staticmethod
    def cree_fichier_si_inexistant(chemin_fichier: Union[str, Path]):
        """
        Crée un fichier s'il n'existe pas déjà.
        Si le répertoire parent n'existe pas, il est créé.
        """
        chemin = Path(chemin_fichier)
        # Crée les répertoires parents si nécessaire
        chemin.parent.mkdir(parents=True, exist_ok=True)
        
        if not chemin.is_file():
            # Crée le fichier si inexistant (touch)
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
        Génère un UUID unique (avec tirets). (Convention de nommage utilisateur).
        """
        return str(uuid.uuid4())
        
    @staticmethod
    def get_guid_brut() -> str:
        """
        Retourne un GUID brut (UUID) sans tirets. (Convention de nommage utilisateur).
        """
        return uuid.uuid4().hex
    
    # --- Réflexion et Vérification ---

    @staticmethod
    def get_function_name() -> str: 
        """
        Retourne le nom du fichier, de la classe et de la fonction appelante (niveau -1)
        sous la forme Fichier/Classe/Méthode.
        (Maintenu pour la traçabilité et la résilience au bug du copier/coller.)
        """
        # Niveau d'inspection (frame 1)
        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            if caller_frame is not None:
                fichier = os.path.basename(caller_frame.f_code.co_filename)
                
                # Heuristique pour déterminer le nom de la classe
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
        (Maintenu pour la traçabilité et la résilience au bug du copier/coller.)
        """
        # Niveau d'inspection (frame 2)
        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            if caller_frame is not None:
                caller2_frame = caller_frame.f_back
                if caller2_frame is not None:
                    fichier = os.path.basename(caller2_frame.f_code.co_filename)
                    
                    # Heuristique pour déterminer le nom de la classe
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

        Justification : Utilisé pour la vérification a priori d'appels facultatifs/dynamiques.
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
        Justification : Utilisé pour la vérification a priori d'appels facultatifs/dynamiques.
        """
        return hasattr(objet, nom_methode)