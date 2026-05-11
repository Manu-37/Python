# BACKLOG — tstat_analyse

> Fichier de référence partagé entre Emmanuel et Claude.
> Mis à jour à chaque fin de session de travail.
> À placer à la racine du repo Git.

---

## 📊 Vision de synthèse

| N   | Tâche                                            | Priorité | Statut      |
|-----|--------------------------------------------------|----------|-------------|
| #3+#6 | Système i18n IHM — CDC établi               | Haute    | En cours    |
| #16 | Exécution `create_ihm_schema.sql`                | Haute    | À faire     |
| #17 | Entités Python schéma `ihm` (14 classes)         | Haute    | À faire     |
| #18 | BaseRef_Manager — UIs gestion référentiel `ihm`  | Haute    | À faire     |
| #19 | Outil d'introspection DB → alimentation `ihm`    | Haute    | À faire     |
| #20 | UI saisie traductions + matrice couverture       | Haute    | À faire     |
| #21 | Générateur JSON chiffré (artefact runtime)       | Haute    | À faire     |
| #22 | `clsI18n` — singleton runtime + bootstrap        | Haute    | À faire     |
| #23 | Intégration `clsI18n` → DataGrid, clsStTableView | Normale  | À faire     |
| #24 | Refonte `clsTableMetadata` → `clsResultMetadata` | Normale  | À faire     |
| #25 | Audit `cree_le`/`modifie_le` toutes les bases    | Basse    | À faire     |
| #14 | Copie de fiche dans Entity_ListView              | Normale  | À faire     |
| #7  | OAuth2 via Freebox                               | Basse    | Différé     |
| #8  | `t_lieu_liu` — lieux manuels                     | Basse    | Différé     |
| #15 | Gestion des colonnes protégées                   | Basse    | Différé     |
| #26 | BaseRef_Manager_2026 — Préférences taille police | Basse    | À faire     |
| #4  | Politique rétention snapshots OneDrive           | Normale  | Terminé     |

---

## 🏗️ Architecture — Principes actés

| Principe | Règle |
|---|---|
| KPI | Un KPI = une méthode = une requête (indépendant et cachable) |
| Arrondi | Dans le controller — données brutes dans les classes stats |
| Timezone | UTC en base, conversion à l'affichage via `zoneinfo` (`Tools.fmt_date`) |
| Formatage | `fmt_date()` et `fmt_float()` dans `Tools` — réexportés depuis `utilis.py` |
| Nommage fonctions | Convention objet_action : `kpi_bloc_format`, `km_par_kwh`... |
| Streamlit width | `use_container_width` déprécié — utiliser `width="stretch"` |
| Scripts SQL | Chaque base dans `db/` a un sous-dossier `sql/` — tout script DDL est accompagné de son script de rollback (`drop_*.sql`) |
| Colonnes d'audit | Toutes les tables sans exception : `{triplet}_cree_le` et `{triplet}_modifie_le` TIMESTAMPTZ + trigger `fn_audit_{triplet}()` BEFORE INSERT OR UPDATE |
| Droits PostgreSQL | Grants toujours sur les rôles (`r_crud`, `r_backup`), jamais sur les utilisateurs — `ALTER DEFAULT PRIVILEGES` obligatoire pour les futurs objets |

### Couche applicative
| Rôle | Fichier |
|---|---|
| Lanceur | `run_tstat_analyse.py` — subprocess + `os.environ` + `cwd` fixé |
| Bootstrap | `cache_ressources.py` — singletons dans le bon processus |
| Cache accueil | `cache_accueil.py` — `@st.cache_data(ttl=300)` |
| Cache charge | `cache_charge.py` — `@st.cache_data(ttl=300)` |
| Contrôleur accueil | `controllers/ctrl_accueil.py` — `kpi_home()`, `serie_energie_par_jour()` |
| Contrôleur charge | `controllers/ctrl_charge.py` — `serie_energie_par_periode()`, `serie_capacite_glissante()`, `serie_sessions()`, `courbe_session()` |
| Design system | `utilis.py` — `COULEURS`, `FONT_SIZE`, `kpi_bloc_format`, `delta_texte`, `delta_couleur`, réexports `fmt_*`, `km_par_kwh` |
| Graphiques | `charts.py` — `fig_energie_km`, `fig_consommation`, `fig_capacite`, `fig_courbe_session` |
| Widgets | `widgets.py` — `ligne_kpi`, `entete_tableau_kpi` |

### Couche DB — classes Q (lecture seule, `db/db_tstat_data/`)
| Classe | MV source | Rôle |
|---|---|---|
| `clsQ_charge_sessions_ext` | MV2 | Sessions brutes — périodes, capacité, kilométrage |
| `clsQ_journee` | MV4 | KPI journaliers — `journee()`, `donnees_periode()`, `moyenne_capacite_glissante()`, `energie_par_jour()`, `capacite_glissante()`, `derniere_capacite()` |

### Vues matérialisées
| # | MV | Source | Rôle |
|---|---|---|---|
| MV1 | `mv_charge_sessions` | `t_snapshot_snp` + `t_charge_chg` | Sessions brutes |
| MV2 | `mv_charge_sessions_ext` | MV1 | + distance inter-charges (LAG) |
| MV3 | `mv_charge_journee` | MV2 | Synthèse par jour de charge |
| MV4 | `mv_journee` | `t_snapshot_snp` | Synthèse quotidienne complète |

> Données exclues : 23 et 24/03/2026 (premiers jours de collecte, incomplets).

---

## 🔄 En cours

### #3+#6 — Système i18n IHM 🔴
**Fusion des tâches #3 (référentiel multilingue) et #6 (refonte clsTableMetadata)**

**CDC établi le 06/05/2026 — architecture validée :**

Remplacement de tous les labels UI éparpillés (dicts `UI_*`, commentaires PostgreSQL, fallbacks hardcodés) par un référentiel centralisé multilingue. Stockage en base (`db_baseref`, schéma `ihm`), distribution sous forme de JSON chiffré par applicatif (via `clsCrypto`), résolution au runtime par un singleton `clsI18n`.

**Architecture :**
```
DB ihm (authoring)  →  [génération manuelle]  →  JSON chiffré par app+langue
                                                         ↓
                                                   clsI18n (singleton)
                                                         ↓
                                              UI (CTK, Streamlit, futur)
```

**Schéma `ihm` — 14 tables validées :**

| Table | Triplet | Rôle |
|---|---|---|
| `t_langue_lan` | `lan` | Langues supportées |
| `t_application_app` | `app` | Applications + entrée `GLOBAL` |
| `t_app_lan_nal` | `nal` | Liaison App ↔ Langue + langue défaut |
| `t_type_element_tel` | `tel` | Types d'éléments UI |
| `t_element_ele` | `ele` | Éléments UI nommés |
| `t_libelle_element_lel` | `lel` | Traductions des éléments UI |
| `t_db_db` | `db` | Bases logiques (racine hiérarchie DB) |
| `t_schema_sch` | `sch` | Schémas PostgreSQL |
| `t_type_relation_tre` | `tre` | Types de relation (TABLE/VIEW/MVIEW) |
| `t_relation_rel` | `rel` | Tables / Vues / Vues matérialisées |
| `t_libelle_relation_lre` | `lre` | Traductions des relations |
| `t_type_affichage_taf` | `taf` | Types d'affichage colonnes |
| `t_colonne_col` | `col` | Colonnes de relation |
| `t_libelle_colonne_lco` | `lco` | Traductions des colonnes |

**Scripts SQL :** `db/db_baseref/sql/create_ihm_schema.sql` + `drop_ihm_schema.sql`

**Périmètre V1 :** colonnes DB, libellés relations, éléments UI (boutons/onglets/titres/sections) — fr actif, en structuré — BaseRef_Manager prioritaire, tstat_analyse ensuite

**Hors périmètre V1 :** messages d'erreur, logs, libellés schémas, bascule langue à chaud, versioning historique

**Sous-tâches ordonnées :** #16 → #17 → #18+#19 → #20 → #21 → #22 → #23 → #24

---

## 📋 À faire

### #16 — Exécution `create_ihm_schema.sql` 🔴
**Scope :** Exécuter le script sur `db_baseref`, vérifier le trigger `fn_audit_ihm()` sur un INSERT test, confirmer les droits `r_crud` et `r_backup`.
**Responsable :** Emmanuel

### #17 — Entités Python schéma `ihm` 🔴
**Scope :** 14 classes dans `db/db_baseref/ihm/` suivant le pattern existant (`clsEntity_ABS`, triplets, getters/setters, `ctrl_valeurs`). Inclut `clsIHM` comme ancre de base (`_DB_SYMBOLIC_NAME = "BASEREF"`).
**Responsable :** Claude
**Dépend de :** #16

### #18 — BaseRef_Manager — UIs gestion référentiel `ihm` 🔴
**Scope :** Interfaces CRUD pour les tables de référence du schéma `ihm` (langues, applications, types, éléments). Discussion préalable sur la présentation générale et la navigation dans une interface qui s'enrichit.
**Responsable :** Claude (avec discussion UI préalable)
**Dépend de :** #17

### #19 — Outil d'introspection DB → alimentation `ihm` 🔴
**Scope :** Lit `pg_catalog` (schemas, tables, vues, colonnes) et alimente automatiquement `t_db_db`, `t_schema_sch`, `t_relation_rel`, `t_colonne_col`. **CDC détaillé obligatoire avant démarrage** — périmètre des bases couvertes, gestion des suppressions/renommages, déclenchement.
**Responsable :** Emmanuel (avec aide Claude)
**Dépend de :** #17

### #20 — UI saisie traductions + matrice de couverture 🔴
**Scope :** Interface de saisie des libellés par élément et par langue. Matrice de couverture ("X clés manquent en japonais"). Baptême du feu du nouveau framework UI.
**Responsable :** Emmanuel
**Dépend de :** #18, #19

### #21 — Générateur JSON chiffré 🔴
**Scope :** Extraction DB → JSON structuré par app+langue → chiffrement Fernet (`clsCrypto`). **CDC détaillé obligatoire** — format JSON, nommage des fichiers, localisation, déclenchement.
**Responsable :** Emmanuel (avec aide Claude)
**Dépend de :** #20

### #22 — `clsI18n` — singleton runtime + bootstrap 🟡
**Scope :** Singleton dans `sysclasses/`. Déchiffrement + chargement JSON au démarrage. `label(cle, locale=None)`, `tooltip(cle, locale=None)`. Fallback chain : app → GLOBAL → clé brute. **CDC détaillé obligatoire.**
**Responsable :** à définir
**Dépend de :** #21

### #23 — Intégration `clsI18n` dans les composants existants 🟡
**Scope :** `clsTableMetadata.get_col_label()` → délègue à `clsI18n`. Correction bug DataGrid (headers affichent `col_name` brut). `clsStTableView` → remplace dicts `UI_*`. Suppression des 5 dicts `UI_*` de `clsQ_charge_sessions_ext`. **CDC détaillé obligatoire.**
**Responsable :** à définir
**Dépend de :** #22

### #24 — Refonte `clsTableMetadata` → `clsResultMetadata` 🟡
**Scope :** Renommage et refonte pour couvrir les résultats de requêtes arbitraires (pas seulement les entités). `clsI18n` doit être stable avant de démarrer. **CDC détaillé obligatoire.**
**Responsable :** à définir
**Dépend de :** #23

### #25 — Colonnes d'audit toutes les bases existantes 🟢
**Scope :** Ajouter `{triplet}_cree_le` / `{triplet}_modifie_le` + trigger `fn_audit_{triplet}()` sur toutes les tables existantes de `db_baseref` (schéma `public`), `db_tstat_data`, `db_tstat_admin`, `db_postgres`. SQL pur, indépendant du reste. Inclut création des dossiers `sql/` manquants.
**Responsable :** Claude (SQL) + Emmanuel (exécution)
**Dépend de :** rien

### #14 — Copie de fiche dans Entity_ListView 🟡
**Scope :** Ajout d'un bouton "Copier" optionnel dans la toolbar (`show_copy_button: bool = False`). Ouvre le formulaire en mode INSERT pré-rempli avec les valeurs de la ligne sélectionnée. PKs identity remises à `None` automatiquement ; PKs manuelles, colonnes chiffrées et FKs conservées telles quelles.

---

## ⏸️ Différé

### #7 — Automatisation callback OAuth2 via Freebox 🟢
**Scope :** `clsTeslaAuth` + infra Freebox — différé sine die

### #8 — `t_lieu_liu` — lieux déclarés manuellement 🟢
**Scope :** SQL + entité — différé sine die

### #26 — BaseRef_Manager_2026 — Préférences taille de police 🟢
**Scope :** Contrôle `+`/`-` dans la barre de menus permettant à l'utilisateur d'ajuster la taille de police globale. Persistance via `QSettings` (Registry Windows, clé `Despont/BaseRefManager2026`). Application immédiate : `AppTheme.FONT_SIZE_DEFAULT` mis à jour + `AppTheme.apply(app_qt)` rappelé. Les fiches déjà ouvertes conservent leur `_hauteur_champ` calculé à la construction — elles se mettent à jour à la prochaine ouverture.
**Responsable :** Claude
**Dépend de :** rien

### #15 — Gestion des colonnes protégées (chiffrées) 🟢
**Scope :** Réflexion sur le concept de colonnes à accès restreint. Aujourd'hui les colonnes `BINARY` (Fernet) sont simplement masquées de l'affichage. À terme : définir une politique de visibilité, de droits et d'édition dans les composants UI — le concept n'est pas encore formalisé.

---

## ✅ Terminé

### #4 — Politique de rétention des sauvegardes OneDrive
**Clôturé le 05/05/2026**

**Contexte :** Les dumps PostgreSQL horaires du serveur Linux (via `backup_postgresql.sh` + rclone) s'accumulent indéfiniment dans `D:\Emmanuel\OneDrive\zLinuxBackup\postgresql\`. La purge locale Linux (48h) existait déjà. Aucune purge côté OneDrive/Windows.

**Solution implémentée :** Remplacement de la logique plate de `BackupCleaner.py` (simple seuil `retention_jours`) par un algorithme GFS complet :

| Fenêtre | Politique |
|---|---|
| < 7 jours | Tout conserver |
| 7–30 jours | Dernier dump de chaque journée |
| 31–365 jours | Dernier dump du dimanche de chaque semaine ISO + dernier dump du dernier jour de chaque mois |
| > 365 jours | Dernier dump du 31 décembre de chaque année |

**Fallback :** si le jour pivot préféré est absent (dimanche, fin de mois, 31/12), on conserve le dernier jour disponible de la période.

**Propriétés de l'algorithme :** date parsée depuis le nom de fichier (pas le `mtime`) → idempotent, gère nativement les purges "en retard" (PC éteint pendant les vacances).

**Fichiers modifiés :**
- `projets/BackupCleaner/BackupCleaner.py` — refonte complète de la purge, v0.1.0
- `projets/BackupCleaner/clsINIBackupCleaner.py` — suppression de `retention_jours`
- `projets/BackupCleaner/Config/BackupCleaner.ini` — suppression de `retention_jours`

---

### #13 — Diagnostic échec jobs pg_cron
**Clôturé le 05/05/2026**

**Cause racine :** pg_cron se connecte à `db_tstat_data` via TCP `localhost`, qui résout en `::1` (IPv6) en priorité sur Debian. `pg_hba.conf` n'avait aucune règle `trust` pour cette combinaison — la règle `scram-sha-256` s'appliquait, et pg_cron échouait faute de mot de passe. Le rôle `postgres` (seul à passer la règle `peer`) avait été désactivé (`NOLOGIN`) pour des raisons de sécurité.

**Correction appliquée dans `/etc/postgresql/15/main/pg_hba.conf` :**
```
local   db_tstat_data   ut_tstat_admin                trust
host    db_tstat_data   ut_tstat_admin   127.0.0.1/32  trust
host    db_tstat_data   ut_tstat_admin   ::1/128       trust
```
Règles ajoutées avant les catch-all `peer` / `scram-sha-256` existantes. Rechargement via `SELECT pg_reload_conf()`. Validé : `status = 'succeeded'`, `return_message = '1 row'`.

---

### #10 — Suivi pg_cron — base + entités + UI
**Clôturé le 04/05/2026**

**Livraisons :**

*Infrastructure DB :*
- `GRANT USAGE ON SCHEMA cron TO ut_tstat` + policies RLS sur `cron.job` et `cron.job_run_details` (visibilité multi-owner)
- Base `postgres` enregistrée dans le catalogue BaseRef_Manager (nom symbolique `POSTGRES`)

*Nouvelles entités (`db/postgres/`) :*
- `clsPostgres` — ancre pour la base `postgres` (`_DB_SYMBOLIC_NAME = "POSTGRES"`)
- `clsJob` — entité lecture seule sur `cron.job` (pas de setters, `ctrl_valeurs` bloquant)
- `clsJob_run_details` — entité lecture seule sur `cron.job_run_details` ; `start_time` et `end_time` convertis en timezone locale via `astimezone()` dans les getters

*Nouvelle UI (BaseRef_Manager) :*
- Bouton **Tâches planifiées** dans la sidebar
- `Job_ListView` — liste des jobs pg_cron (lecture seule, sans boutons CRUD)
- `Job_run_details_ListView` — 100 dernières exécutions du job sélectionné, triées `start_time DESC`, filtrées par `jobid` via `where_clause`

*Améliorations framework déclenchées par cette tâche :*
- `clsEntity_ABS.load_all()` — nouveaux paramètres `where_clause` et `limit` (`FETCH FIRST n ROWS ONLY`, actif uniquement si `order_by` présent)
- `Entity_ListView` — nouveaux paramètres `show_crud_buttons`, `nb_lignes_max`, `where_clause`, `sash_ratio` ; toolbar non rendue si vide
- `clsTableMetadata.get_col_width()` — correction calcul largeur pour entiers binaires PostgreSQL (precision en bits) : `SMALLINT`→70px, `INTEGER`→100px, `BIGINT`→140px
- `clsSQL_Postgre._TYPE_MAPPING` — ajout du type système PostgreSQL `name`

---

### #12 — Sauvegarde `db_tstat_data` — correction droits séquences
**Clôturé le 03/05/2026**

**Cause racine :** `r_backup` n'avait pas `SELECT` sur les séquences de `db_tstat_data` (`permission denied for sequence t_snapshot_snp_snp_id_seq`). Le droit `CONNECT` pour `ut_backup` était déjà en place — le dump échouait silencieusement (fichier 0 KB produit puis rejeté).

**Correction appliquée (sur `db_tstat_data`) :**
```sql
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO r_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO r_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO r_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO r_backup;
```
**Validé :** cycle complet dump + upload OneDrive sans erreur (`erreurs: 0`).

### #2 — Page charge
**Livraisons :**
- **Onglet Recharge** : énergie + km par granularité (jour/semaine/mois selon durée), courbe consommation kWh/100km, comparaison période précédente avec recalcul auto de la date, tableau KPI récapitulatif
- **Onglet Capacité** : évolution batterie estimée sur période (Mois à Année), moyenne glissante adaptative au changement de durée (14→30→45→60j), étiquettes axe X adaptées (semaines dd/mm pour Trimestre, mois français pour Semestre/Année), "Semaine" exclue (trop court pour l'analyse de capacité)
- **Onglet Sessions récentes** : liste paginée des sessions de charge avec durée, kWh, SOC début→fin, puissance max, type AC/DC, km depuis charge précédente ; sélection d'une ligne → courbe de charge (puissance kW + SOC % en fonction du temps)
- Composant réutilisable `selecteurs_periode()` — paramètre `durees`, nb_points adaptatif via session_state, recalcul auto date de comparaison
- Correction bug `mv_charge_sessions` — sessions fantômes (3 causes cumulatives)

### #5 — Refactoring architecture + #11 — Restructuration `__init__.py`
**Livraisons :**
- Nouvelle hiérarchie DB : `clsDB_ABS` → `clsStat_ABS` / `clsEntity_ABS` → `clsTstatData_STAT` → classes Q
- `clsTstatCharge`, `clsTstatBase`, `clsStatBase` supprimés
- `clsQ_journee` (MV4) et `clsQ_charge_sessions_ext` (MV2) créées dans `db/db_tstat_data/public/`
- `mv_journee` enrichie : `odometer_delta_miles` (natif miles), `odometer_debut/fin` depuis snapshots, colonnes MV3 via LEFT JOIN
- `clsQ_charge_journee` (MV3) supprimée — absorbée dans `clsQ_journee`
- `controllers/ctrl_accueil.py` créé — `kpi_home()` et `serie_energie_par_jour()`
- Convention `__init__.py` appliquée : `from projets.tstat_analyse import kpi_home` — structure interne opaque
- `db/__init__.py` et `projets/__init__.py` supprimés (dossiers groupants, pas des packages)

| N  | Tâche                                          | Notes                                                                        |
|----|------------------------------------------------|------------------------------------------------------------------------------|
| —  | Prise en main repo Git                         | Framework sysclasses, BaseRef_Manager, tstat_collecteur, db                  |
| —  | Refonte logs                                   | `clsLOG.py` — version finale                                                 |
| —  | snp_soc + vue matérialisée                     | `clsFrequenceManager.py` + `clsCollecteur.py` — versions finales             |
| —  | Architecture Streamlit                         | Structure validée, cache opérationnel, bootstrap subprocess                  |
| —  | Theme sombre                                   | `config.toml` + `cwd` fixé dans `run_tstat_analyse.py`                       |
| —  | MV3 `mv_charge_journee`                        | Synthèse quotidienne + refresh orchestré + collecteur mis à jour             |
| —  | Design system `utilis.py`                      | `COULEURS`, `FONT_SIZE`, `kpi_bloc_format`, `delta_texte`, `delta_couleur`   |
| —  | `fmt_float` / `fmt_date` / `km_par_kwh`        | Génériques — réexportés depuis `utilis.py`                                   |
| —  | Selecteur véhicule                             | `st.selectbox` + `get_liste_vehicules()` dans `cache_charge.py`              |
| #1 | Page d'accueil v1->v2                          | KPIs journée/mois/année, capacité 7j avec delta, rendement km, graphique     |
| #9 | `mv_journee` + graphique km                    | MV4 snapshots, détection coupure réseau collecteur, double axe Y accueil     |
| #5 | Refactoring architecture — dette technique     | Voir détail ci-dessus                                                        |
| #11| Restructuration `__init__.py`                  | Voir détail ci-dessus                                                        |
| #2 | Page charge — 3 onglets                        | Voir détail ci-dessus                                                        |
| #10 | Suivi pg_cron                                 | Base postgres + entités RO + UI double datagrid + améliorations FWK          |
| #12 | Sauvegarde `db_tstat_data`                   | Droits SELECT séquences manquants sur `r_backup` — corrigé 03/05/2026        |
| #13 | Diagnostic échec jobs pg_cron                | pg_cron → TCP IPv6 (::1) sans règle trust — 3 règles pg_hba.conf ajoutées — corrigé 05/05/2026 |

---

## 💡 Conventions de travail

**Priorités :**
- 🔴 Haute — en cours ou bloquant
- 🟡 Normale — prochaine itération
- 🟢 Basse — différé ou optionnel

**Workflow :**
1. Début de session → lire `BACKLOG.md` + fichiers concernés
2. Fin de session → mettre à jour `BACKLOG.md` ensemble
3. Committer `BACKLOG.md` avec le code à chaque fin de session
