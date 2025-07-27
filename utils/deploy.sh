#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

APP_DEST="/opt/arrosage"
WWW_DEST="/var/www/arrosage"
TMP_CLONE="/tmp/arrosage"
BACKUP_DIR="/opt/arrosage_backup"

log() {
    echo -e "\n### $1 ###"
}

abort() {
    echo "❌ Erreur à l'étape '$1'. Arrêt du script."
    exit 1
}

trap 'abort "${BASH_COMMAND}"' ERR

log "Préparation du répertoire temporaire"
rm -rf "$TMP_CLONE"
git clone git@github.com:vincent-ledu/arrosage.git "$TMP_CLONE"

log "Sauvegarde de la configuration et de la base de données"
sudo mkdir -p "$BACKUP_DIR"
sudo cp -f "$APP_DEST/config.json" "$BACKUP_DIR/" || true
sudo cp -f "$APP_DEST/arrosage.db" "$BACKUP_DIR/" || true

log "Activation de la maintenance"
sudo touch "$WWW_DEST/MAINTENANCE"

log "Mise à jour de la configuration Nginx"
sudo cp "$TMP_CLONE/deployment/nginx/arrosage.conf" /etc/nginx/sites-available/
sudo cp "$TMP_CLONE/deployment/nginx/maintenance.html" "$WWW_DEST/"
sudo nginx -t && sudo systemctl restart nginx

log "Arrêt des services"
sudo systemctl stop gunicorn_arrosage.service

log "Suppression de l'ancienne version"
sudo rm -rf "$APP_DEST"
sudo mkdir -p "$APP_DEST"

log "Déploiement de la nouvelle version"
sudo cp -r "$TMP_CLONE/app/." "$APP_DEST/"
sudo rm -rf "$APP_DEST/.git"

log "Restauration des données"
sudo cp -f "$BACKUP_DIR/config.json" "$APP_DEST/" || echo "⚠️ config.json non restauré"
sudo cp -f "$BACKUP_DIR/arrosage.db" "$APP_DEST/" || echo "⚠️ arrosage.db non restauré"
sudo chown -R www-data:www-data "$APP_DEST"

log "Initialisation de l’environnement Python"
cd "$APP_DEST"
sudo -u www-data python3 -m venv .venv
sudo -u www-data .venv/bin/pip install -r requirements.txt
sudo -u www-data .venv/bin/pybabel compile -d translations

log "Nettoyage des fichiers temporaires"
sudo rm -rf "$APP_DEST/tests"
sudo rm -rf "$BACKUP_DIR"

log "Redémarrage des services"
sudo systemctl start gunicorn_arrosage.service

log "Vérification de l'état de santé"

MAX_ATTEMPTS=3
for i in $(seq 1 $MAX_ATTEMPTS); do
    sleep 1
    if curl -sif --unix-socket /run/gunicorn/gunicorn_arrosage.sock http://localhost/health | grep -q '200 OK'; then
        echo "✅ Gunicorn OK"
        sudo rm -f $WWW_DEST/MAINTENANCE
        break
    elif [ "$i" -eq "$MAX_ATTEMPTS" ]; then
        echo "❌ SERVICE NON DISPONIBLE après $MAX_ATTEMPTS tentatives — maintenance toujours activée"
        exit 1
    fi
done

log "Déploiement terminé avec succès 🎉"
