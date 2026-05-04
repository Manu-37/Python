# BACKLOG — tstat_analyse

> Fichier de référence partagé entre Emmanuel et Claude.
> Mis à jour à chaque fin de session de travail.
> À placer à la racine du repo Git.

---

## 📊 Vision de synthèse

| N   | Tâche                                      | Priorité | Statut   |
|-----|--------------------------------------------|----------|----------|
| #13 | Diagnostic échec jobs pg_cron              | BUG 🔴  | À faire  |
| #10 | Suivi pg_cron — base + entités + UI        | Normale  | Terminé  |
| #4  | Politique rétention snapshots              | Normale  | À faire  |
| #7  | OAuth2 via Freebox                         | Basse    | À faire  |
| #2  | Page charge                                | Normale  | Terminé  |
| #3  | Référentiel colonnes multilingue           | Basse    | Différé  |
| #6  | Refonte `clsTableMetadata`                 | Basse    | Différé  |
| #8  | `t_lieu_liu` — lieux manuels               | Basse    | Différé  |

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

*(aucune tâche en cours)*

---

## 📋 À faire

### #13 — Diagnostic échec jobs pg_cron 🔴
**Scope :** Base `postgres` — schéma `cron`

**Symptôme :** Tous les jobs pg_cron échouent systématiquement à chaque exécution (visible dans `cron.job_run_details`, colonne `return_message`).

**Hypothèse principale :** Problème de droits — l'utilisateur d'exécution des jobs (à identifier dans `cron.job.username`) n'a pas les privilèges nécessaires sur `db_tstat_data` pour exécuter les fonctions de rafraîchissement des MV.

**Investigation à mener :**
1. Lire `return_message` des dernières exécutions échouées pour identifier le message d'erreur exact
2. Vérifier l'utilisateur d'exécution (`username` dans `cron.job`)
3. Vérifier les droits de cet utilisateur sur les objets ciblés (`REFRESH MATERIALIZED VIEW`, fonctions, schéma)
4. Corriger les droits manquants

---

### #4 — Politique rétention snapshots — purge automatique 🟡
**Scope :** Freebox uniquement

### #7 — Automatisation callback OAuth2 via Freebox 🟢
**Scope :** `clsTeslaAuth` + infra Freebox

---

## ⏸️ Différé

### #3 — Référentiel colonnes multilingue 🟢
**Scope :** Remplacement des dicts UI rustine par un vrai référentiel multilingue

### #6 — Refonte `clsTableMetadata` → `clsResultMetadata` 🟢
**Scope :** Impact massif sur toute la couche UI — à traiter quand la base est stabilisée

### #8 — `t_lieu_liu` — lieux déclarés manuellement 🟢
**Scope :** SQL + entité — différé sine die

---

## ✅ Terminé

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
| #10 | Suivi pg_cron                                  | Base postgres + entités RO + UI double datagrid + améliorations FWK          |
| #12 | Sauvegarde `db_tstat_data`                    | Droits SELECT séquences manquants sur `r_backup` — corrigé 03/05/2026        |

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
