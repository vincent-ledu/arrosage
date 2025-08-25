#!/usr/bin/env bash
set -euo pipefail

### --------- PARAMÈTRES À ADAPTER ---------
# Racine de déploiement (stable)
APP_ROOT="/opt/arrosage"
RELEASES_DIR="$APP_ROOT/releases"
CURRENT_LINK="$APP_ROOT/current"
SHARED_DIR="$APP_ROOT/shared"

# Service systemd
SYSTEMD_SERVICE="gunicorn_arrosage.service"

# URL de healthcheck (mets un endpoint très léger, ex: /healthz)
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1/healthz}"

# Utilisateur/groupe qui exécute le service
APP_USER="www-data"
APP_GROUP="www-data"

# Dossier racine du repo (ce script est censé se trouver dans utils/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Python / venv par release (recommandé pour l’atomicité)
PYTHON_BIN="${PYTHON_BIN:-python3}"
PIP_OPTS="${PIP_OPTS:---no-cache-dir}"

# Exclusions de copie (inutile en prod)
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


# Anti double-run
mkdir -p "$APP_ROOT"
exec 9> "$APP_ROOT/deploy.lock"
if ! flock -n 9; then
  log "⚠️ [deploy] Un déploiement est déjà en cours."
  exit 1
fi

TS="$(timestamp)"
NEW_RELEASE="$RELEASES_DIR/$TS"

log "ℹ️ [deploy] Préparation des dossiers…"
mkdir -p "$RELEASES_DIR" "$SHARED_DIR"/{log,run,config,db,backups}
# Exemple : si tu veux un venv partagé, crée-le dans $SHARED_DIR/venv et ajuste plus bas.
# Ici on fait un venv par release, pour des rollbacks plus clean.

log "ℹ️ [deploy] Copie du code vers $NEW_RELEASE…"
mkdir -p "$NEW_RELEASE"
rsync -a "${RSYNC_EXCLUDES[@]}" "$REPO_ROOT/app"/ "$NEW_RELEASE"/

log "ℹ️ [deploy] Création du venv…"
$PYTHON_BIN -m venv "$NEW_RELEASE/.venv"
# shellcheck disable=SC1091
source "$NEW_RELEASE/.venv/bin/activate"

log "ℹ️ [deploy] Mise à jour de pip…"
pip install $PIP_OPTS --upgrade pip wheel

log "ℹ️ [deploy] Configuration des variables d’environnement…"
set -a
source /etc/default/arrosage
set +a 

log "ℹ️ [deploy] DATABASE_URL=${DATABASE_URL:-<non défini>}"


log "ℹ️ [deploy] Mise en place du backup de la base de données…"
cp $REPO_ROOT/utils/backup_arrosage.sh /usr/local/bin/backup_arrosage.sh
chmod +x /usr/local/bin/backup_arrosage.sh
# Ajoute une tâche cron pour le backup quotidien à 3h17 du matin  
LINE='17 3 * * * /usr/local/bin/backup_arrosage.sh'
USER=root
( crontab -u "$USER" -l 2>/dev/null | grep -Fv "$LINE" ; echo "$LINE" ) | crontab -u "$USER" -

log "ℹ️ [deploy] Backup de la base de données…"
if command -v /usr/local/bin/backup_arrosage.sh >/dev/null 2>&1; then
  /usr/local/bin/backup_arrosage.sh
else
  log "❌ [deploy] Script de backup non trouvé, pas de backup effectué."
  exit 1
fi

log "ℹ️ [deploy] Installation des dépendances…"
if [[ -f "$NEW_RELEASE/requirements.txt" ]]; then
  pip install $PIP_OPTS -r "$NEW_RELEASE/requirements.txt"
fi

log "ℹ️ [deploy] Upgrade Alembic (migrations)…"
if command -v alembic >/dev/null 2>&1 && [[ -f "$NEW_RELEASE/alembic.ini" ]]; then
  (cd "$NEW_RELEASE" && alembic upgrade head || true)
else
  log "⚠️ [deploy] Alembic non trouvé ou pas de migrations à appliquer."
fi

# (Optionnel) i18n si présent
if command -v pybabel >/dev/null 2>&1 && [[ -d "$NEW_RELEASE/translations" ]]; then
  log "ℹ️ [deploy] Compilation i18n…"
  (cd "$NEW_RELEASE" && pybabel compile -d translations || true)
fi

# Liens vers les ressources "shared" (config, base, logs…)
# ⚠️ Adapte les chemins cibles dans le code Flask si nécessaire.
log "ℹ️ [deploy] Liaison des ressources partagées…"
# Exemple: config.json attendu par l'app
if [[ ! -f "$SHARED_DIR/config/config.json" ]]; then
  echo '{}' > "$SHARED_DIR/config/config.json"
fi
ln -sfn "$SHARED_DIR/config/config.json" "$NEW_RELEASE/config.json"

# Logs (app + gunicorn) dans shared/log
mkdir -p "$SHARED_DIR/log"
ln -sfn "$SHARED_DIR/log" "$NEW_RELEASE/log"

# Permissions
log "ℹ️ [deploy] Permissions…"
chown -R "$APP_USER:$APP_GROUP" "$APP_ROOT"

# Swap atomique du symlink + rollback si healthcheck KO
PREV_TARGET="$(readlink -f "$CURRENT_LINK" || true)"

log "ℹ️ [deploy] Bascule du symlink…"
ln -sfn "$NEW_RELEASE" "$CURRENT_LINK"

log "ℹ️ [deploy] Restart du service…"
systemctl restart "$SYSTEMD_SERVICE"

log "ℹ️ [deploy] Healthcheck ($HEALTHCHECK_URL)…"
ok=0
for i in 1 2 3; do
  sleep 1
  if curl -fsS "$HEALTHCHECK_URL" >/dev/null 2>&1; then
    ok=1
    break
  fi
  log "⚠️ [deploy] tentative $i/3 échouée, nouvel essai…"
done

if [[ $ok -ne 1 ]]; then
  log "❌ [deploy] ÉCHEC healthcheck → rollback…"
  if [[ -n "${PREV_TARGET:-}" && -d "$PREV_TARGET" ]]; then
    ln -sfn "$PREV_TARGET" "$CURRENT_LINK"
    systemctl restart "$SYSTEMD_SERVICE" || true
    log "⚠️ [deploy] Rollback effectué vers: $PREV_TARGET"
  else
    log "⚠️ [deploy] Pas de release précédente valide pour rollback."
  fi
  exit 1
fi

log " ✅ [deploy] Succès : release active → $NEW_RELEASE"
exit 0
