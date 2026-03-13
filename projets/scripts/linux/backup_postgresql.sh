#!/bin/bash

# ============================================================
# backup_postgresql.sh
# Sauvegarde automatique des bases PostgreSQL vers OneDrive
# ============================================================

# --- Configuration ---
BACKUP_DIR="/home/freebox/backups"
RCLONE_REMOTE="onedrive_backup:zLinuxBackup/postgresql"
PG_USER="ut_backup"
PG_ROLE="r_backup"
PG_HOST="localhost"
RETENTION_HOURS=48
LOG_FILE="/home/freebox/backups/backup.log"

# --- Fonctions ---
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# --- Début ---
log "========== Début sauvegarde =========="

# Récupère la liste des bases accessibles par ut_backup
BASES=$(psql -U "$PG_USER" -h "$PG_HOST" -d postgres -t -A -c "
    SELECT datname FROM pg_database
    WHERE has_database_privilege('ut_backup', datname, 'CONNECT')
    AND datname NOT IN ('postgres', 'template0', 'template1');
")

if [ -z "$BASES" ]; then
    log "ERREUR : aucune base trouvée"
    exit 1
fi

# --- Boucle sur chaque base ---
ERREUR=0
for BASE in $BASES; do
    HORODATAGE=$(date '+%Y%m%d_%H%M%S')
    FICHIER="${BACKUP_DIR}/${BASE}_${HORODATAGE}.dump"

    log "Dump de $BASE vers $FICHIER"
    pg_dump -U "$PG_USER" -h "$PG_HOST" --role="$PG_ROLE" -F c -f "$FICHIER" "$BASE"

    if [ $? -eq 0 ]; then
        log "Dump $BASE OK"
        rclone copy "$FICHIER" "$RCLONE_REMOTE/$BASE/"
        if [ $? -eq 0 ]; then
            log "Upload $BASE OK"
        else
            log "ERREUR upload $BASE"
            ERREUR=1
        fi
    else
        log "ERREUR dump $BASE"
        ERREUR=1
    fi
done

# --- Purge locale ---
log "Purge des dumps locaux > ${RETENTION_HOURS}h"
find "$BACKUP_DIR" -name "*.dump" -mmin +$((RETENTION_HOURS * 60)) -delete

log "========== Fin sauvegarde (erreurs: $ERREUR) =========="
exit $ERREUR