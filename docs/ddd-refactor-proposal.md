# Proposition de refonte Domain-Driven Design

## Constats sur l'existant

* `app/app.py` concentre la configuration Flask, des appels HTTP externes, des accès SQLAlchemy et la gestion temps-réel du matériel (pompe, vannes, flotteurs). 【F:app/app.py†L1-L454】
* Les accès à la base (`app/db`) exposent directement l'ORM aux couches supérieures, ce qui couple l'API au schéma relationnel. 【F:app/db/db_tasks.py†L18-L80】
* Le contrôle matériel est instancié en global selon l'environnement, ce qui rend difficile le remplacement dans des scénarios métiers. 【F:app/app.py†L25-L37】

Ces éléments mélangent responsabilités applicatives, domaine et infrastructure, compliquant l'évolution vers de nouvelles règles d'arrosage.

## Bounded contexts proposés

| Contexte | Responsabilité | Entités / Agrégats | Interfaces externes |
| --- | --- | --- | --- |
| **WateringControl** | Pilotage des tâches d'arrosage (durée, annulation, statut) | `WateringTask`, `WateringSchedule` | GPIO/contrôleur matériel |
| **WaterResource** | Mesure et alerte sur le niveau d'eau disponible | `TankLevel`, `WaterAvailability` | Capteurs de niveau |
| **WeatherInsight** | Collecte et agrégation des prévisions météo | `DailyForecast`, `PartDayForecast` | API Open-Meteo |
| **SystemConfiguration** | Paramétrage utilisateur (coordonnées, mois actifs, seuils) | `WateringPolicy` | Fichier de configuration |

Chaque contexte expose des services applicatifs explicites et des ports (interfaces) vers l'infrastructure.

## Strate d'architecture (hexagone inspiré DDD)

```
domain/
  watering/
    entities.py        # WateringTask, TankLevelSnapshot
    policies.py        # Règles métier (mois actifs, températures)
    services.py        # e.g. WateringScheduler
  weather/
    value_objects.py
    services.py        # Agrégations sur les prévisions
  configuration/
    repositories.py    # Port vers le stockage de configuration
application/
  watering/
    commands.py        # StartWatering, StopWatering
    queries.py         # FetchCurrentTask
    handlers.py        # Orchestration des entités et ports
infrastructure/
  persistence/
    watering_task_repository.py
    weather_repository.py
  devices/
    gpio_controller.py
  external/
    open_meteo_client.py
interfaces/
  http/
    flask/
      routes/
  cli/
```

* **Domain** : entités riches, règles (`WateringPolicy`) calculant la durée selon la température, validations de disponibilité d'eau.
* **Application** : orchestrateurs qui orchestrent les ports (`WateringTaskRepository`, `WeatherForecastProvider`, `DeviceController`). Les commandes/queries remplacent les routes lourdes de `app/app.py`. 【F:app/app.py†L280-L433】
* **Infrastructure** : implémentations SQLAlchemy/GPIO/API des ports. `db_tasks` devient une implémentation de `WateringTaskRepository`. 【F:app/db/db_tasks.py†L18-L80】
* **Interfaces** : routes Flask deviennent de simples adaptateurs qui traduisent HTTP ↔ commandes applicatives.

## Ports et adapters clés

| Port | Contrat | Adapter initial |
| --- | --- | --- |
| `DeviceController` | `open_water(duration)`, `close_water()`, `read_tank_level()` | `GPIOControl` / `FakeControl` (déplacés sous `infrastructure.devices`) 【F:app/app.py†L25-L37】|
| `WateringTaskRepository` | CRUD des tâches, recherche par statut | `db_tasks` (renommé, injecté) 【F:app/db/db_tasks.py†L18-L80】|
| `ForecastProvider` | Récupération des prévisions brutes | `services.weather.fetch_open_meteo` |
| `ForecastCache` | Stockage court-terme des prévisions agrégées | `db_forecast_data`, `db_weather_data` |
| `ConfigurationRepository` | Lecture/écriture des paramètres | `config.config` |

## Règles métier explicitées

1. **Validation de fenêtre d'arrosage** : isoler dans `WateringPolicy.can_start_watering(month, min_temperature, tank_level)` les règles dispersées sur la route `/api/command/open-water`. 【F:app/app.py†L343-L405】
2. **Gestion des tâches** : encapsuler la logique d'annulation et d'update dans un service `WateringTaskManager` afin d'éviter le couplage au threading dans l'adapter HTTP. 【F:app/app.py†L280-L414】
3. **Agrégation météo** : déplacer l'appel Open-Meteo dans un `ForecastService` qui gère fraicheur & persistence. 【F:app/app.py†L115-L214】

## Stratégie de migration

1. **Cartographier** les routes existantes vers des cas d'usage (e.g. `OpenWaterDelay` → commande `StartManualWatering`).
2. **Introduire** les ports (interfaces) dans un nouveau module `domain` tout en continuant d'utiliser les implémentations existantes.
3. **Déplacer progressivement** la logique métier dans les services du domaine en ajoutant des tests unitaires ciblés (durées, autorisations, validations température).
4. **Créer** une fine couche application (handlers) orchestrant les ports; adapter les routes Flask pour appeler ces handlers.
5. **Refactoriser** les modules `db_*`, `control_*`, `services.weather` en adaptateurs conformes aux ports, sans modifier immédiatement les dépendances externes.
6. **Nettoyer** `app/app.py` pour n'y laisser que le bootstrap Flask, l'injection des dépendances et le wiring des routes.

## Livrables intermédiaires recommandés

* Tests de régression sur les routes critiques (`/api/command/open-water`, `/api/water-level`, `/api/forecast`).
* Documentation d'architecture actualisée décrivant les contextes et ports.
* Scripts de migration de la base si le modèle d'entité `WateringTask` évolue.

Cette approche permet d'encapsuler la logique métier, de préparer l'ajout de nouvelles règles (par exemple volume pompé par arrosage) et de faciliter la substitution des capteurs ou de l'API météo.
