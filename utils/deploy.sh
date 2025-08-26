#!/usr/bin/env bash
set -euo pipefail

### --------- PARAMETERS TO ADAPT ---------
# Deployment root (stable)
APP_ROOT="/opt/arrosage"
RELEASES_DIR="$APP_ROOT/releases"
CURRENT_LINK="$APP_ROOT/current"
SHARED_DIR="$APP_ROOT/shared"

# systemd service
SYSTEMD_SERVICE="gunicorn_arrosage.service"

# Healthcheck URL (use a very lightweight endpoint, e.g.: /healthz)
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1/healthz}"

# User/group running the service
APP_USER="www-data"
APP_GROUP="www-data"

# Repo root folder (this script is supposed to be in utils/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Python / venv per release (recommended for atomicity)
PYTHON_BIN="${PYTHON_BIN:-python3}"
PIP_OPTS="${PIP_OPTS:---no-cache-dir}"

# Copy exclusions (useless in prod)
RSYNC_EXCLUDES=(
  --exclude ".git/"
  --exclude ".github/"
  --exclude ".venv/"
  --exclude "tests/"
)
### ----------------------------------------

timestamp() { date -u +"%Y%m%dT%H%M%SZ"; }

log() {
 echo $(date +"%Y-%m-%d %T") $1 
}

# Prevent double-run
mkdir -p "$APP_ROOT"
exec 9> "$APP_ROOT/deploy.lock"
if ! flock -n 9; then
  log "⚠️ [deploy] A deployment is already in progress."
  exit 1
fi

TS="$(timestamp)"
NEW_RELEASE="$RELEASES_DIR/$TS"

log "ℹ️ [deploy] Preparing folders…"
mkdir -p "$RELEASES_DIR" "$SHARED_DIR"/{log,run,config,db,backups}
# Example: if you want a shared venv, create it in $SHARED_DIR/venv and adjust below.
# Here we use a venv per release, for cleaner rollbacks.

log "ℹ️ [deploy] Copying code to $NEW_RELEASE…"
mkdir -p "$NEW_RELEASE"
rsync -a "${RSYNC_EXCLUDES[@]}" "$REPO_ROOT/app"/ "$NEW_RELEASE"/

log "ℹ️ [deploy] Creating venv…"
$PYTHON_BIN -m venv "$NEW_RELEASE/.venv"
# shellcheck disable=SC1091
source "$NEW_RELEASE/.venv/bin/activate"

log "ℹ️ [deploy] Updating pip…"
pip install $PIP_OPTS --upgrade pip wheel

log "ℹ️ [deploy] Configuring environment variables…"
set -a
source /etc/default/arrosage
set +a 

log "ℹ️ [deploy] DATABASE_URL=${DATABASE_URL:-<undefined>}"

log "ℹ️ [deploy] Setting up database backup…"
cp $REPO_ROOT/utils/backup_arrosage.sh /usr/local/bin/backup_arrosage.sh
chmod +x /usr/local/bin/backup_arrosage.sh
# Add a daily cron job for backup at 3:17 AM  
LINE='17 3 * * * /usr/local/bin/backup_arrosage.sh'
USER=root
( crontab -u "$USER" -l 2>/dev/null | grep -Fv "$LINE" ; echo "$LINE" ) | crontab -u "$USER" -

log "ℹ️ [deploy] Database backup…"
if command -v /usr/local/bin/backup_arrosage.sh >/dev/null 2>&1; then
  /usr/local/bin/backup_arrosage.sh
else
  log "❌ [deploy] Backup script not found, no backup performed."
  exit 1
fi

log "ℹ️ [deploy] Installing dependencies…"
if [[ -f "$NEW_RELEASE/requirements.txt" ]]; then
  pip install $PIP_OPTS -r "$NEW_RELEASE/requirements.txt"
fi

log "ℹ️ [deploy] Alembic upgrade (migrations)…"
if command -v alembic >/dev/null 2>&1 && [[ -f "$NEW_RELEASE/alembic.ini" ]]; then
  (cd "$NEW_RELEASE" && alembic upgrade head || true)
else
  log "⚠️ [deploy] Alembic not found or no migrations to apply."
fi

# (Optional) i18n if present
if command -v pybabel >/dev/null 2>&1 && [[ -d "$NEW_RELEASE/translations" ]]; then
  log "ℹ️ [deploy] Compiling i18n…"
  (cd "$NEW_RELEASE" && pybabel compile -d translations || true)
fi

# Symlinks to "shared" resources (config, db, logs…)
# ⚠️ Adjust target paths in Flask code if needed.
log "ℹ️ [deploy] Linking shared resources…"
# Example: config.json expected by the app
if [[ ! -f "$SHARED_DIR/config/config.json" ]]; then
  echo '{}' > "$SHARED_DIR/config/config.json"
fi
ln -sfn "$SHARED_DIR/config/config.json" "$NEW_RELEASE/config.json"

# Logs (app + gunicorn) in shared/log
mkdir -p "$SHARED_DIR/log"
ln -sfn "$SHARED_DIR/log" "$NEW_RELEASE/log"

# Permissions
log "ℹ️ [deploy] Setting permissions…"
chown -R "$APP_USER:$APP_GROUP" "$APP_ROOT"

# Atomic symlink swap + rollback if healthcheck fails
PREV_TARGET="$(readlink -f "$CURRENT_LINK" || true)"

log "ℹ️ [deploy] Switching symlink…"
ln -sfn "$NEW_RELEASE" "$CURRENT_LINK"

log "ℹ️ [deploy] Restarting service…"
systemctl restart "$SYSTEMD_SERVICE"

log "ℹ️ [deploy] Healthcheck ($HEALTHCHECK_URL)…"
ok=0
for i in 1 2 3; do
  sleep 1
  if curl -fsS "$HEALTHCHECK_URL" >/dev/null 2>&1; then
    ok=1
    break
  fi
  log "⚠️ [deploy] attempt $i/3 failed, retrying…"
done

if [[ $ok -ne 1 ]]; then
  log "❌ [deploy] Healthcheck FAILED → rollback…"
  if [[ -n "${PREV_TARGET:-}" && -d "$PREV_TARGET" ]]; then
    ln -sfn "$PREV_TARGET" "$CURRENT_LINK"
    systemctl restart "$SYSTEMD_SERVICE" || true
    log "⚠️ [deploy] Rollback performed to: $PREV_TARGET"
  else
    log "⚠️ [deploy] No valid previous release for rollback."
  fi
  exit 1
fi

log "ℹ️ [deploy] Cleaning up old releases (keeping last 5)…"
ls -1dt "$RELEASES_DIR"/* | tail -n +6 | xargs -r rm -rf

log " ✅ [deploy] Success: active release → $NEW_RELEASE"
exit 0
