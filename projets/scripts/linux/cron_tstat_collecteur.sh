#!/bin/bash
# =============================================================================
# cron_tstat_collecteur.sh
# Lanceur cron pour tstat_collecteur — Freebox Linux ARM64 Debian
# =============================================================================
#
# Installation cron (crontab -e) :
#   */5 * * * * /home/freebox/Python/projets/tstat_collecteur/cron_tstat_collecteur.sh
#
# Ce script :
#   1. Active l'environnement Python correct
#   2. Lance tstat_collecteur.py
#   3. Redirige les sorties vers le log cron (distinct du log applicatif)
#
# Le log applicatif (clsLOG) est géré par le Python lui-même.
# Ce log cron ne capture que les erreurs de lancement (Python absent, etc.)
# =============================================================================

# --- Chemins ---
PYTHON_DIR="/home/freebox/Python"
SCRIPT="$PYTHON_DIR/projets/tstat_collecteur/tstat_collecteur.py"
LOG_CRON="$PYTHON_DIR/projets/tstat_collecteur/logs/cron.log"

# --- Création du dossier logs si absent ---
mkdir -p "$(dirname "$LOG_CRON")"

# --- Lancement ---
# python3 : Python système (3.13 installé globalement sur la Freebox)
# 2>&1    : stderr redirigé vers stdout → tout dans le même fichier log
echo "$(date '+%Y-%m-%d %H:%M:%S') | Lancement cron" >> "$LOG_CRON"

cd "$PYTHON_DIR" && python3 "$SCRIPT" >> "$LOG_CRON" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ERREUR exit code=$EXIT_CODE" >> "$LOG_CRON"
fi