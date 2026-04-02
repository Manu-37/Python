# BACKLOG — tstat_analyse

> Fichier de référence partagé entre Emmanuel et Claude.
> Mis à jour à chaque fin de session de travail.
> À placer à la racine du repo Git.

---

## 🏗️ Architecture — Rappel des principes actés

| Principe | Règle |
|---|---|
| KPI | Un KPI = une méthode = une requête (indépendant et cachable) |
| Arrondi | Dans le controller — données brutes dans `clsTstatCharge` |
| Timezone | UTC en base, conversion à l'affichage via `zoneinfo` |
| Formatage | `fmt_date()` et `fmt_float()` à extraire dans `utils.py` dès que la page d'accueil est stable |

### Couche applicative
| Rôle | Fichier |
|---|---|
| Lanceur | `run_tstat_analyse.py` — subprocess + `os.environ` |
| Bootstrap | `cache.py/_bootstrap()` — singletons dans le bon processus |
| Cache | `cache.py` — `@st.cache_resource` / `@st.cache_data(ttl=300)` |
| Vues génériques | `sysclasses/ui/streamlit/` — `clsStView`, `clsStChartView`, `clsStTableView`, `clsStFilterView` |
| Vues spécialisées | `tstat_analyse/ui/` |
| Stats | `tstat_analyse/clsTstatBase.py` + `tstat_analyse/clsTstatCharge.py` |

---

## 🔄 En cours

### #1 — Mise au point page d'accueil 🔴
**Scope :** `Accueil.py` + `clsTstatCharge` + `utils.py`

**Contexte :** `Accueil.py` tourne et affiche des données réelles issues de `clsTstatCharge` via la couche cache Streamlit. L'architecture est validée. Il reste à fiabiliser les données affichées et affiner la présentation avant de passer à la page suivante.

**Sous-tâches dans l'ordre :**
- [ ] 1. Valider tous les KPI scalaires — valeurs, arrondis, unités
- [ ] 2. Valider le graphique énergie par jour — période, format axe X, hover
- [ ] 3. Affiner la disposition — groupement thématique des KPI, colonnes
- [ ] 4. Ajouter le delta SOC 7j vs 7j précédents — nécessite `_soc_glissant` avec fenêtre décalée dans `clsTstatCharge`
- [ ] 5. Valider la conso kWh/100km — cohérence numérateur/dénominateur
- [ ] 6. Extraire `fmt_date()` et `fmt_float()` dans `utils.py` — réutilisation pages suivantes

**Fichiers de référence pour cette tâche :**
- `Accueil.py`
- `clsTstatCharge.py`
- `cache.py`
- `clsLOG.py`
- `utils.py` (si déjà amorcé)
- `run_tstat_analyse.py`

---

## 📋 À faire

### #2 — Page charge 🟡
**Scope :** `01_Charge.py` + `cls01_Charge.py` + filter + chart + table

### #3 — Référentiel colonnes multilingue 🟡
**Scope :** Remplacement des dicts UI rustine par un vrai référentiel multilingue

### #4 — Politique rétention snapshots — purge automatique 🟡
**Scope :** Freebox uniquement

### #5 — Dette technique — couche contrôleur/service 🟡
**Scope :** Architecture globale

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
| — | Architecture Streamlit + page d'accueil | Structure validée, cache opérationnel |
| — | Deux décisions d'architecture | Actées et intégrées dans les principes ci-dessus |

---

## 💡 Conventions de travail

**Priorités :**
- 🔴 Haute — en cours ou bloquant
- 🟡 Normale — prochaine itération
- 🟢 Basse — différé ou optionnel

**Workflow :**
1. Début de session → partager ce fichier + les fichiers concernés
2. Fin de session → mettre à jour ce fichier ensemble
3. Committer `BACKLOG.md` avec le code à chaque fin de session