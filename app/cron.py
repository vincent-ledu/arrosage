import sys
import requests
from config import load_config
import logging


# Configuration globale du logger
logging.basicConfig(
  level=logging.DEBUG,  # DEBUG pour + de détails
  format="%(asctime)s [%(levelname)s] %(message)s",
  handlers=[
    logging.FileHandler("/var/log/gunicorn/cron-arrosage.log"),   # Log dans un fichier
    logging.StreamHandler()                # Log dans la console aussi
  ]
)
logger = logging.getLogger(__name__)

# Vérifier si un argument a été passé pour 'morning' ou 'evening'
if len(sys.argv) != 2 or sys.argv[1] not in ['morning', 'evening']:
    print("Usage: python script.py [morning|evening]")
    sys.exit(1)

# Récupérer l'argument 'morning' ou 'evening'
time_of_day = sys.argv[1]

# Récupérer les coordonnées depuis l'application Flask

# Configuration des en-têtes pour la requête
headers = {
    "X-Real-IP": "192.168.0.105"
}

watering_config = load_config()["watering"]

# Récupération du type d'arrosage
watering_type_res = requests.get("http://localhost/api/watering-type", headers=headers)

logger.info(f"Watering type: {watering_type_res.text}")
watering_type = watering_type_res.text
duration = watering_config[watering_type][time_of_day + "-duration"]
if (duration is None or duration <= 0):
    logger.warning(f"No duration specified for watering type {watering_type} on {time_of_day}.")
    sys.exit(0)

logger.info(f"Call for watering {time_of_day}...")
response_arrosage = requests.get(f"http://localhost/api/command/open-water?duration={duration}", headers=headers)
logger.info(response_arrosage.raise_for_status())
logger.info(f"Watering done on {time_of_day} for {duration} seconds.")
