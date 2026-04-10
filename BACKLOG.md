# BACKLOG — tstat_analyse

> Fichier de référence partagé entre Emmanuel et Claude.
> Mis à jour à chaque fin de session de travail.
> À placer à la racine du repo Git.

---

## 📊 Vision de synthèse

| N  | Tâche                                      | Priorité | Statut        |
|----|--------------------------------------------|----------|---------------|
| #5 | Refactoring architecture — dette technique | HAUTE    | A faire       |
| #9 | `mv_journee` — vue quotidienne complète    | HAUTE    | Termine       |
| #2 | Page charge                                | Normale  | Bloque par #5 |
| #3 | Référentiel colonnes multilingue           | Normale  | A faire       |
| #4 | Politique rétention snapshots              | Normale  | A faire       |
| #6 | Refonte `clsTableMetadata`                 | Basse    | Differe       |
| #7 | OAuth2 via Freebox                         | Basse    | A faire       |
| #8 | `t_lieu_liu` — lieux manuels               | Basse    | Differe       |

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
| Bootstrap | `cache_ressources.py/_bootstrap()` — singletons dans le bon processus |
| Cache | `cache_charge.py` — `@st.cache_resource` / `@st.cache_data(ttl=300)` |
| Design system | `utilis.py` — `COULEURS`, `FONT_SIZE`, `kpi_bloc_format`, `delta_texte`, `delta_couleur`, réexports `fmt_*`, `km_par_kwh` |
| Stats sessions | `clsTstatCharge` — source `mv_charge_sessions_ext` |
| Stats journalières | `clsTstatCharge` — source `mv_charge_journee` (MV3) |
| Contrôleurs | `controllers/` — un fichier par page (à implémenter — #5) |

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

### #5 — Refactoring architecture — dette technique 🔴
**Scope :** Architecture globale — à faire AVANT la page #2

**Travaux identifiés :**
- Découper `clsTstatCharge` en deux classes :
  - `clsTstatSessionsExt` — source `mv_charge_sessions_ext`
  - `clsTstatJournee` — source `mv_charge_journee`
- Créer `controllers/ctrl_accueil.py` — assembleur + formatage final (conversions miles→km, calcul conso)
- Réduire `accueil.py` à du pur `st.*` — zéro calcul, zéro logique métier
- Supprimer `clsTstatCharge` si vidée de son contenu

### #2 — Page charge 🟡
**Scope :** `01_Charge.py` + contrôleur + filter + chart + table
**Dépend de :** #5

### #3 — Référentiel colonnes multilingue 🟡
**Scope :** Remplacement des dicts UI rustine par un vrai référentiel multilingue

### #4 — Politique rétention snapshots — purge automatique 🟡
**Scope :** Freebox uniquement

### #7 — Automatisation callback OAuth2 via Freebox 🟢
**Scope :** `clsTeslaAuth` + infra Freebox

---

## ⏸️ Différé

### #6 — Refonte `clsTableMetadata` → `clsResultMetadata` 🟢
**Scope :** Impact massif sur toute la couche UI — à traiter quand la base est stabilisée

### #8 — `t_lieu_liu` — lieux déclarés manuellement 🟢
**Scope :** SQL + entité — différé sine die

---

## ✅ Terminé

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
