# BACKLOG — tstat_analyse

> Fichier de référence partagé entre Emmanuel et Claude.
> Mis à jour à chaque fin de session de travail.
> À placer à la racine du repo Git.

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
| Bootstrap | `cache.py/_bootstrap()` — singletons dans le bon processus |
| Cache | `cache.py` — `@st.cache_resource` / `@st.cache_data(ttl=300)` |
| Design system | `utilis.py` — `COULEURS`, `FONT_SIZE`, `kpi_bloc_format`, réexports `fmt_*`, `km_par_kwh` |
| Stats sessions | `clsTstatCharge` — source `mv_charge_sessions_ext` |
| Stats journalières | `clsTstatCharge` — source `mv_charge_journee` (MV3) |
| Contrôleurs | `controllers/` — un fichier par page (à implémenter — #5) |

### Vues matérialisées
| MV | Source | Rôle |
|---|---|---|
| `mv_charge_sessions` | `t_snapshot_snp` + `t_charge_chg` | Sessions brutes |
| `mv_charge_sessions_ext` | MV1 | + distance inter-charges (LAG) |
| `mv_charge_journee` | MV2 | Synthèse quotidienne — agrégation par jour de début |

> Données exclues : 23 et 24/03/2026 (premiers jours de collecte, incomplets).
> Prévu mi-avril : exclure tout le mois de mars.

---

## 🔄 En cours

### #1 — Finalisation page d'accueil 🔴
**Scope :** `accueil.py` + `clsTstatCharge` + `utilis.py`

**Contexte :** Page opérationnelle avec données réelles. Thème sombre actif.
Design system `utilis.py` en place. Il reste à valider visuellement le rendu
final et ajouter `km_par_kwh` dans l'affichage.

**Sous-tâches restantes :**
- [ ] Valider `km_par_kwh` ajouté par Emmanuel dans `Tools` + `utilis.py`
- [ ] Intégrer `km_par_kwh` dans l'affichage (journée, mois, année)
- [ ] Valider visuellement que tout tient sur un écran 27" 2K

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

| # | Tâche | Notes |
|---|---|---|
| — | Prise en main repo Git | Framework sysclasses, BaseRef_Manager, tstat_collecteur, db |
| — | Refonte logs | `clsLOG.py` — version finale |
| — | snp_soc + vue matérialisée | `clsFrequenceManager.py` + `clsCollecteur.py` — versions finales |
| — | Architecture Streamlit | Structure validée, cache opérationnel, bootstrap subprocess |
| — | Thème sombre | `config.toml` + `cwd` fixé dans `run_tstat_analyse.py` |
| — | MV3 `mv_charge_journee` | Synthèse quotidienne + refresh orchestré + collecteur mis à jour |
| — | Design system `utilis.py` | `COULEURS`, `FONT_SIZE`, `kpi_bloc_format()` |
| — | `fmt_float` / `fmt_date` dans `Tools` | Génériques — réexportés depuis `utilis.py` |
| — | Sélecteur véhicule | `st.selectbox` + `get_liste_vehicules()` dans `cache.py` |
| #1 | Page d'accueil v1→v2 | KPIs journée/mois/année, capacité 7j avec delta, graphique énergie |

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
