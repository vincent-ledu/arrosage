"""Script de cron pour l'arrosage automatique basé sur la configuration.
   Ce script est destiné à être exécuté périodiquement via cron pour
   gérer l'arrosage automatique en fonction des paramètres définis dans
   l'application Flask."""
import sys
import os
import logging
import requests
import config.config as local_config


# Configuration globale du logger
_testing_mode = os.getenv("TESTING") == "1"

_handlers = [logging.StreamHandler()]
if not _testing_mode:
    _handlers.insert(0, logging.FileHandler("/var/log/gunicorn/cron-arrosage.log"))

logging.basicConfig(
    level=logging.DEBUG if _testing_mode else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_handlers,
    force=True,
)
logger = logging.getLogger(__name__)


def watering(time_of_day):
    """ Récupérer les coordonnées depuis l'application Flask
        Configuration des en-têtes pour la requête"""
    headers = {"X-Real-IP": "192.168.0.105"}

    watering_config = local_config.load_config()["watering"]
    logger.info("Loaded watering configuration: %s", watering_config)

    # Récupération du type d'arrosage
    watering_type_res = requests.get(
        "http://localhost/api/watering-type", headers=headers, timeout=5
    )
    watering_type = watering_type_res.text
    logger.info("Watering type: %s", watering_type)
    duration = watering_config[watering_type][time_of_day + "-duration"]
    logger.info("Duration for %s at %s: %s seconds", watering_type, time_of_day, duration)
    if duration is None or duration <= 0:
        logger.warning(
            "No duration specified for watering type %s on %s.", watering_type, time_of_day
        )
        sys.exit(0)

    logger.info("Call for watering %s...", time_of_day)
    response_arrosage = requests.get(
        f"http://localhost/api/command/open-water?duration={duration}", headers=headers, timeout=5
    )
    if response_arrosage.status_code != 200:
        logger.error(
            "Error during watering request: %s - %s",
            response_arrosage.status_code,
            response_arrosage.text,
        )
        sys.exit(1)
    logger.info("Watering done on %s for %s seconds.", time_of_day, duration)


if __name__ == "__main__":
    # Vérifier si un argument a été passé pour 'morning' ou 'evening'
    if len(sys.argv) != 2 or sys.argv[1] not in ["morning", "evening"]:
        logger.error("Usage: python script.py [morning|evening]")
        sys.exit(1)
    time_of_day = sys.argv[1]
    watering(time_of_day)
