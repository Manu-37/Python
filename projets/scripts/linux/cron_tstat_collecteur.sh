#!/bin/bash
# =============================================================================
# cron_tstat_collecteur.sh
# Lanceur cron pour tstat_collecteur — Freebox Linux ARM64 Debian
# =============================================================================
#
# Installation cron (crontab -e) :
#   */5 * * * * /home/freebox/Python/projets/scripts/linux/cron_tstat_collecteur.sh
#
# Rôle unique : lancer tstat_collecteur.py dans le bon répertoire de travail.
# Tout le logging est géré par clsLOG dans le Python — pas de log bash ici.
# L'UUID dans chaque ligne de log permet de distinguer chaque exécution cron.
# =============================================================================

PYTHON_DIR="/home/freebox/Python"
SCRIPT="$PYTHON_DIR/projets/tstat_collecteur/tstat_collecteur.py"

cd "$PYTHON_DIR" && python3 "$SCRIPT"