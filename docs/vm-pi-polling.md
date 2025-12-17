# VM side – Pi polling & cache

Objectif : l’UI/back reste disponible même si le Raspberry Pi est instable.
La VM poll périodiquement le `pi-service` et stocke le dernier état connu en DB.

## Variables d’environnement (VM)

Dans `/etc/default/arrosage` :

- `PI_SERVICE_URL=http://<pi-host>` (obligatoire pour activer le mode Pi)
- `PI_SERVICE_TOKEN=...` (recommandé)
- `PI_SERVICE_TIMEOUT_CONNECT=0.5`
- `PI_SERVICE_TIMEOUT_READ=1.0`
- `PI_SNAPSHOT_MAX_AGE_SEC=120`

## Cache en base

- Table `device_snapshot` : dernier état connu (niveau d’eau, watering, last_seen_at…)
- Table `device_command_log` : audit des commandes start/stop

Migration Alembic : `migrations/versions/7_0f1caa2f4cbb_create_device_snapshot_and_logs.py`

## Poller

Script : `scripts/pi_poll.py`

Option systemd timer (recommandé) :

- Service : `deployment/systemd/arrosage-pi-poll.service`
- Timer : `deployment/systemd/arrosage-pi-poll.timer`

Installation (sur la VM) :

- `sudo cp /opt/arrosage/current/deployment/systemd/arrosage-pi-poll.service /etc/systemd/system/`
- `sudo cp /opt/arrosage/current/deployment/systemd/arrosage-pi-poll.timer /etc/systemd/system/`
- `sudo systemctl daemon-reload`
- `sudo systemctl enable --now arrosage-pi-poll.timer`

## Endpoints VM

- `GET /api/water-level` : sert le cache DB (fallback 0 si pas de cache)
- `GET /api/device/snapshot` : détail du snapshot + stale/age
- `GET /api/device/gpio?verbose=1` : proxy live vers le Pi (si disponible)

