# CLAUDE.md

Ce fichier fournit des indications à Claude Code (claude.ai/code) pour travailler dans ce dépôt.

## Convention de langue

**Tout le code, les commentaires, les noms de variables, les noms de fonctions et les messages de commit sont en français.** C'est une convention stricte appliquée dans l'ensemble du projet.

## Vue d'ensemble

Monorepo Python multi-projets dédié à la télémétrie des véhicules Tesla : collecte, stockage, analyse et gestion de la configuration. Utilise PostgreSQL comme SGBDR (via psycopg2), Streamlit pour les tableaux de bord, et CustomTkinter pour les interfaces desktop.

## Lancement des applications

```bash
# Tableau de bord analytique Streamlit (ouvre http://localhost:8501)
python projets/tstat_analyse/run_tstat_analyse.py

# Collecteur de données Tesla (normalement piloté par le Planificateur de tâches Windows toutes les 5 min)
python -m projets.tstat_collecteur.tstat_collecteur

# Gestionnaire de configuration desktop (GUI CustomTkinter)
python projets/BaseRef_Manager/BaseRef_Manager.py

# Utilitaire de nettoyage des sauvegardes (normalement piloté par le Planificateur de tâches Windows quotidiennement)
python projets/BackupCleaner/BackupCleaner.py
```

## Tests

Pas de configuration pytest formelle. Les tests se trouvent dans `projets/zzz tests/` (ignoré par git) et `sysclasses/test_divers.py`. Installation des dépendances : `pip install -r requirements.txt`.

## Architecture

### Organisation du monorepo

- `sysclasses/` — framework partagé (logs, DB, config, chiffrement, widgets UI)
- `db/` — modèles entités organisés par schéma (`db_baseref/`, `db_tstat_admin/`, `db_tstat_data/`)
- `projets/` — les quatre applications + `shared/` (utilitaires API Tesla)
- `logs/` — fichiers de logs rotatifs, un sous-répertoire par projet

### Pattern Bootstrap (critique)

Chaque application démarre via `AppBootstrap` (`sysclasses/AppBootstrap.py`), qui initialise les singletons dans un ordre fixe et obligatoire :

1. Sous-classe de `clsINICommun` — config INI du projet
2. `clsINISecurity` — lecture du `security.ini` (absent du git, contient les identifiants chiffrés)
3. `clsLOG` — journalisation
4. `clsCrypto` — chiffrement/déchiffrement Fernet
5. `clsDBAManager` — connexions base de données + tunnels SSH optionnels
6. `clsEmailManager` — SMTP

Cet ordre ne peut pas être modifié. Le mode bootstrap (`'ui'`, `'console'` ou `'streamlit'`) détermine comment les erreurs fatales sont affichées. Ne jamais initialiser ces singletons manuellement en dehors de AppBootstrap.

### Fichiers de configuration

Chaque projet possède `Config/{nom_projet}.ini` avec les sections `[ENVIRONNEMENT]`, `[LOG]` et une ou plusieurs sections `[EMAIL_*]`. Les données sensibles (mots de passe DB, tokens OAuth, clé de chiffrement) se trouvent dans `security.ini`, dont le chemin est indiqué par la clé `path` dans `[ENVIRONNEMENT]`. Le fichier `security.ini` n'est jamais commité.

### Utilisation des singletons

Tous les composants du framework (`clsLOG`, `clsDBAManager`, `clsINI*`) sont des singletons : le premier appel initialise, les appels suivants retournent l'instance existante. Toujours passer par `AppBootstrap` ; ne jamais instancier directement.

### Base de données et couche d'accès

Le `clsDBAManager` assure un support **multibases simultané** : plusieurs bases de données peuvent être connectées et utilisées en parallèle au sein d'une même application, chacune avec sa propre connexion gérée de façon indépendante. Il ne vise pas la requête interbase, qui n'est pas son propos. L'implémentation actuelle utilise PostgreSQL via `clsSQL_Postgre` (`sysclasses/clsSQL_Postgre.py`). **L'architecture est conçue pour supporter d'autres SGBDR** : il suffit de créer une classe driver suivant le même pattern que `clsSQL_Postgre` et de l'enregistrer dans le manager.

Les classes entités dans `db/` héritent de `clsEntity_ABS` (`db/clsEntity_ABS.py`). Toutes les opérations d'insertion/mise à jour appellent `ctrl_valeurs()` pour la validation avant tout accès DB. Deux niveaux de validation :
- `ErreurValidationBloquante` — bloque l'opération
- `AvertissementValidation` — avertissement uniquement

Le schéma `db_baseref` est le catalogue maître. `db_tstat_admin` contient les véhicules et les tokens OAuth Tesla. `db_tstat_data` contient les données opérationnelles (snapshots, sessions de charge, sessions de conduite).

### Pattern subprocess Streamlit

`run_tstat_analyse.py` lance `streamlit run accueil.py` en sous-processus, en passant les constantes de bootstrap via des variables d'environnement. Le véritable `AppBootstrap` s'exécute dans `projets/tstat_analyse/cache.py::_bootstrap()`, uniquement dans le processus Streamlit. Cela permet au script lanceur de rester léger.

### Tunnels SSH

`clsDBAManager` crée automatiquement des tunnels SSH lorsque l'IP cliente diffère de l'IP du serveur de base de données. Aucune gestion manuelle du tunnel n'est nécessaire — tout est transparent à la connexion.

### Rotation des logs

`clsLOG` utilise un `_TimestampedFileHandler` personnalisé : les fichiers de log sont nommés `log_YYYYMMDD_HHMMSS.log` et rotatifs par taille (pas par durée). Des alertes email se déclenchent sur des événements CRITICAL répétés.

### Verrou anti-chevauchement (tstat_collecteur)

Le collecteur écrit un fichier `.lock` contenant son PID. Au démarrage, si le verrou existe et que le PID est toujours actif, il s'arrête proprement. Cela évite les exécutions cron simultanées.
