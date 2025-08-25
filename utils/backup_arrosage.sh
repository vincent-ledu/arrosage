#!/usr/bin/env bash
set -euo pipefail
source /etc/default/arrosage

# Read database variables from /etc/default/arrosage
# Expected variables: MARIADB_HOST, MARIADB_USER, MARIADB_PASSWORD, MARIADB_DATABASE, MARIADB_BACKUP_LOCATION

DBUSER=wateringdevuser
DBPASSWORD=password
DBHOST=localhost
DBPORT=3306
DBNAME=wateringdev
DBOPTIONS="charset=utf8mb4"
DBDRIVER="mysql+pymysql"

DB_HOST="${DBHOST:-localhost}"
DB_USER="${DBUSER:-root}"
DB_PASS="${DBPASSWORD:-}"
DB_NAME="${DBNAME:-watering}"
DST="${BACKUP_LOCATION:-/opt/arrosage/shared/backups}"

log() {
  echo "$(date +"%Y-%m-%d %T") $1"
}

log "ℹ️ [backup] Starting MariaDB backup..."
log "ℹ️ [backup] Database: $DB_NAME"
log "ℹ️ [backup] Backup directory: $DST"
mkdir -p "$DST"

BACKUP_FILE="$DST/${DB_NAME}_$(date +%F_%H%M%S).sql.gz"

mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$BACKUP_FILE"

find "$DST" -type f -mtime +14 -delete

log "ℹ️ [backup] Backup completed successfully."
log "ℹ️ [backup] Backups older than 14 days have been deleted."
log "ℹ️ [backup] Current backups: $(ls -lh $DST)"
