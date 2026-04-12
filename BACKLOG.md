# BACKLOG — tstat_analyse

> Fichier de référence partagé entre Emmanuel et Claude.
> Mis à jour à chaque fin de session de travail.
> À placer à la racine du repo Git.

---

## 📊 Vision de synthèse

| N   | Tâche                                      | Priorité | Statut        |
|-----|--------------------------------------------|----------|---------------|
| #5  | Refactoring architecture — dette technique | HAUTE    | Terminé       |
| #11 | Restructuration `__init__.py`              | HAUTE    | Terminé       |
| #2  | Page charge                                | Normale  | Bloque par #5 |
| #10 | Suivi pg_cron — base + entités + UI        | Normale  | A faire       |
| #4  | Politique rétention snapshots              | Normale  | A faire       |
| #7  | OAuth2 via Freebox                         | Basse    | A faire       |
| #3  | Référentiel colonnes multilingue           | Basse    | Differe       |
| #6  | Refonte `clsTableMetadata`                 | Basse    | Differe       |
| #8  | `t_lieu_liu` — lieux manuels               | Basse    | Differe       |

---

## 🏗️ Architecture — Principes actés

| Principe | Règle |
|---|---|
| KPI | Un KPI = une méthode = une requête (indépendant et cachable) |
| Arrondi | Dans le controller — données brutes dans les classes stats |
| Timezone | UTC en base, conversion à l'affichage via `zoneinfo` (`Tools.fmt_date`) |
| Formatage | `fmt_date()` et `fmt_float()` dans `Tools` — réexportés depuis `utilis.py` |
| Nommage fonctions | Convention objet_action : `kpi_bloc_format`, `km_par_kwh`... |

### Couche applicative
| Rôle | Fichier |
|---|---|
| Lanceur | `run_tstat_analyse.py` — subprocess + `os.environ` + `cwd` fixé |
| Bootstrap | `cache_ressources.py` — singletons dans le bon processus |
| Cache | `cache_charge.py` — `@st.cache_data(ttl=300)`, importe via `projets.tstat_analyse` |
| Contrôleur accueil | `controllers/ctrl_accueil.py` — `kpi_home()`, `serie_energie_par_jour()` |
| Design system | `utilis.py` — `COULEURS`, `FONT_SIZE`, `kpi_bloc_format`, `delta_texte`, `delta_couleur`, réexports `fmt_*`, `km_par_kwh` |

### Couche DB — classes Q (lecture seule, `db/db_tstat_data/`)
| Classe | MV source | Rôle |
|---|---|---|
| `clsQ_charge_sessions_ext` | MV2 | Sessions brutes — périodes, capacité, kilométrage |
| `clsQ_journee` | MV4 | KPI journaliers — `journee()`, `donnees_periode()`, `moyenne_capacite_glissante()`, `energie_par_jour()`, `derniere_capacite()` |

### Vues matérialisées
| # | MV | Source | Rôle |
|---|---|---|---|
| MV1 | `mv_charge_sessions` | `t_snapshot_snp` + `t_charge_chg` | Sessions brutes |
| MV2 | `mv_charge_sessions_ext` | MV1 | + distance inter-charges (LAG) |
| MV3 | `mv_charge_journee` | MV2 | Synthèse par jour de charge |
| MV4 | `mv_journee` | `t_snapshot_snp` | Synthèse quotidienne complète |

> Données exclues : 23 et 24/03/2026 (premiers jours de collecte, incomplets).
> Prévu mi-avril : exclure tout le mois de mars.

---

## 🔄 En cours

*(aucune tâche en cours)*

---

## 📋 À faire

### #2 — Page charge 🟡
**Scope :** `01_Charge.py` + contrôleur + filter + chart + table
**Dépend de :** #5

### #10 — Suivi pg_cron — base + entités + UI 🟡
**Scope :** BaseRef_Manager — nouvelle section de monitoring des rafraîchissements des MV

**Contexte :** pg_cron stocke l'historique d'exécution des jobs dans sa propre base `postgre`, schéma `cron`. L'objectif est d'exposer ces données dans le BaseRef_Manager pour surveiller les refreshes programmés des vues matérialisées.

**Travaux identifiés :**
1. **Connexion PostgreSQL** — déclarer la base `postgre` (schéma `cron`) dans le gestionnaire de bases (`clsDBAManager`) avec le compte `ut_tstat`. Vérifier préalablement que `ut_tstat` a bien les droits `SELECT` sur `cron.job` et `cron.job_run_details` (`\dp cron.job` dans psql, ou `GRANT SELECT ON cron.job, cron.job_run_details TO ut_tstat;` si nécessaire).
2. **Dossier `db/cron/`** — créer les entités `clsJob` et `clsJobRunDetails` héritant de `clsEntity_ABS`, en mode lecture seule (pas d'insert/update).
3. **UI BaseRef_Manager** — nouvelle section ou onglet affichant la liste des jobs pg_cron et leur dernière exécution (statut, durée, message d'erreur éventuel).

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
| #5 | Refactoring architecture — dette technique     | Voir détail ci-dessous                                                       |
| #11| Restructuration `__init__.py`                  | Voir détail ci-dessous                                                       |

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
