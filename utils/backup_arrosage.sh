#!/usr/bin/env bash
set -euo pipefail
source /etc/default/arrosage
DB=$DATABASE_LOCATION
DST=$DATABASE_BACKUP_LOCATION

log() {
 echo $(date +"%Y-%m-%d %T") $1 
}

log "ℹ️ [backup] Starting database backup..."
log "ℹ️ [backup] Database: $DB"
log "ℹ️ [backup] Backup directory: $DST"
mkdir -p "$DST"
sqlite3 "$DB" "VACUUM;"            # compact
cp -a "$DB" "$DST/$(date +%F_%H%M%S).db"
find "$DST" -type f -mtime +14 -delete
log "ℹ️ [backup] Backup completed successfully."
log "ℹ️ [backup] Backups older than 14 days have been deleted."
log "ℹ️ [backup] Current backups: $(ls -lh $DST)"