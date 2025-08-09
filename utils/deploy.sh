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

# Anti double-run
mkdir -p "$APP_ROOT"
exec 9> "$APP_ROOT/deploy.lock"
if ! flock -n 9; then
  echo "[deploy] Un déploiement est déjà en cours."
  exit 1
fi

TS="$(timestamp)"
NEW_RELEASE="$RELEASES_DIR/$TS"

echo "ℹ️ [deploy] Préparation des dossiers…"
mkdir -p "$RELEASES_DIR" "$SHARED_DIR"/{log,run,config,db}
# Exemple : si tu veux un venv partagé, crée-le dans $SHARED_DIR/venv et ajuste plus bas.
# Ici on fait un venv par release, pour des rollbacks plus clean.

echo "ℹ️ [deploy] Copie du code vers $NEW_RELEASE…"
mkdir -p "$NEW_RELEASE"
rsync -a "${RSYNC_EXCLUDES[@]}" "$REPO_ROOT/app"/ "$NEW_RELEASE"/

echo "ℹ️ [deploy] Création du venv…"
$PYTHON_BIN -m venv "$NEW_RELEASE/.venv"
# shellcheck disable=SC1091
source "$NEW_RELEASE/.venv/bin/activate"

echo "ℹ️ [deploy] Installation des dépendances…"
if [[ -f "$NEW_RELEASE/requirements.txt" ]]; then
  pip install $PIP_OPTS -r "$NEW_RELEASE/requirements.txt"
fi

# (Optionnel) i18n si présent
if command -v pybabel >/dev/null 2>&1 && [[ -d "$NEW_RELEASE/app/translations" ]]; then
  echo "ℹ️ [deploy] Compilation i18n…"
  (cd "$NEW_RELEASE" && pybabel compile -d app/translations || true)
fi

# Liens vers les ressources "shared" (config, base, logs…)
# ⚠️ Adapte les chemins cibles dans le code Flask si nécessaire.
echo "ℹ️ [deploy] Liaison des ressources partagées…"
# Exemple: config.json attendu par l'app
if [[ ! -f "$SHARED_DIR/config/config.json" ]]; then
  echo '{}' > "$SHARED_DIR/config/config.json"
fi
ln -sfn "$SHARED_DIR/config/config.json" "$NEW_RELEASE/app/config.json"

# Exemple: base SQLite (créée si absente)
if [[ ! -f "$SHARED_DIR/db/arrosage.db" ]]; then
  touch "$SHARED_DIR/db/arrosage.db"
fi
ln -sfn "$SHARED_DIR/db/arrosage.db" "$NEW_RELEASE/app/arrosage.db"

# Logs (app + gunicorn) dans shared/log
mkdir -p "$SHARED_DIR/log"
ln -sfn "$SHARED_DIR/log" "$NEW_RELEASE/log"

# Permissions
echo "ℹ️ [deploy] Permissions…"
chown -R "$APP_USER:$APP_GROUP" "$APP_ROOT"

# Swap atomique du symlink + rollback si healthcheck KO
PREV_TARGET="$(readlink -f "$CURRENT_LINK" || true)"

echo "ℹ️ [deploy] Bascule du symlink…"
ln -sfn "$NEW_RELEASE" "$CURRENT_LINK"

echo "ℹ️ [deploy] Restart du service…"
systemctl restart "$SYSTEMD_SERVICE"

echo "ℹ️ [deploy] Healthcheck ($HEALTHCHECK_URL)…"
ok=0
for i in 1 2 3; do
  sleep 1
  if curl -fsS "$HEALTHCHECK_URL" >/dev/null 2>&1; then
    ok=1
    break
  fi
  echo "⚠️ [deploy] tentative $i/3 échouée, nouvel essai…"
done

if [[ $ok -ne 1 ]]; then
  echo "❌ [deploy] ÉCHEC healthcheck → rollback…"
  if [[ -n "${PREV_TARGET:-}" && -d "$PREV_TARGET" ]]; then
    ln -sfn "$PREV_TARGET" "$CURRENT_LINK"
    systemctl restart "$SYSTEMD_SERVICE" || true
    echo "⚠️ [deploy] Rollback effectué vers: $PREV_TARGET"
  else
    echo "⚠️ [deploy] Pas de release précédente valide pour rollback."
  fi
  exit 1
fi

echo " ✅ [deploy] Succès : release active → $NEW_RELEASE"
exit 0
