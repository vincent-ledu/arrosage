# Pi Service (Device Agent) – REST Contract

Objectif : service **minimaliste** sur Raspberry Pi, **sans DB** et sans UI, qui pilote uniquement le GPIO.

## Sécurité / sûreté (recommandations)

- **Arrêt automatique local (timer)** : toute commande de démarrage doit planifier un arrêt côté Pi (même si le réseau tombe).
- **Durée max** : refuser les durées > `PI_MAX_WATERING_DURATION_SEC` (défaut `900` = 15 minutes).
- **Auth simple** : token en header (`Authorization: Bearer <token>` ou `X-API-Token: <token>`), via `PI_SERVICE_TOKEN`.
- **Allowlist LAN** : recommandé via Nginx (ou firewall) pour limiter l’accès aux endpoints de commande.

## Endpoints

### Health
- `GET /healthz` → `200` si le service répond et le GPIO est joignable.

### Niveau d’eau
- `GET /v1/water-level` → `200`
  - Réponse : `{ "level_percent": 0|25|50|75|100, "ts": "..." }`

### Statut arrosage
- `GET /v1/status` → `200`
  - Réponse :
    - `watering`: bool
    - `remaining_sec`: int
    - `since`, `scheduled_stop_at`: ISO8601 ou `null`
    - `water_level_percent`: int

### Démarrer
- `POST /v1/watering/start` → `202`
  - Body JSON : `{ "duration_sec": 60 }`
  - Header optionnel : `Idempotency-Key: <uuid|string>`
  - Erreurs :
    - `400` durée manquante / invalide / > max
    - `409` si déjà en cours (sauf idempotence)

### Stop
- `POST /v1/watering/stop` → `200`
  - Réponse : `{ "stopped": true|false }`

### GPIO (config + état)
- `GET /v1/gpio` → `200`
  - Réponse par défaut : pins configurés
  - `?verbose=1` : ajoute `levels_state` (lecture GPIO des capteurs) + `outputs` (état logique pump/valve)

## Lancer le service (dev)

Dans ce repo, le code est sous `src/` (comme en prod où `src/` est copié à la racine du release).
Pour lancer depuis la racine du repo :

- `(.venv) gunicorn --chdir src pi_service.wsgi:app --bind 0.0.0.0:8000`

Variables usuelles :

- `ARROSAGE_CONFIG_FILE=/etc/arrosage/config.json`
- `PI_SERVICE_TOKEN=...`
- `PI_MAX_WATERING_DURATION_SEC=900`

## Déploiement (systemd + nginx)

- Unité systemd : `deployment/systemd/arrosage-pi.service`
  - Socket gunicorn : `unix:/run/gunicorn/gunicorn_arrosage_pi.sock`
- Nginx : `deployment/nginx/arrosage-pi.conf`
  - `/healthz` et `/healthcheck` ouverts
  - le reste est restreint au LAN (RFC1918), à adapter à ton plan d’adressage
- Fichier d’environnement : `deployment/etc/default/arrosage-pi`
  - `ARROSAGE_CONFIG_FILE` doit pointer vers le `config.json` local au Pi
