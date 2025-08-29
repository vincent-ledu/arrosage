# config.py
import json
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "pump": 2,
    "valve": 3,
    "levels": [7, 8, 9, 10],
    "watering": {
    "low": {
      "threshold": 15,
      "morning-duration": 30,
      "evening-duration": 30
    },
    "moderate": {
      "threshold": 20,
      "morning-duration": 45,
      "evening-duration": 45
    },
    "standard": {
      "threshold": 25,
      "morning-duration": 60,
      "evening-duration": 60
    },
    "reinforced": {
      "threshold": 30,
      "morning-duration": 75,
      "evening-duration": 75
    },
    "high": {
      "threshold": 35,
      "morning-duration": 90,
      "evening-duration": 90
    }
  },
  "coordinates": {
    "latitude": 48.866667,
    "longitude": 2.333333
  }
}
# mysql+pymysql://wateringdevuser:password@localhost:3306/wateringdev
DBUSER=os.getenv("DBUSER", "wateringdevuser")
DBPASSWORD=os.getenv("DBPASSWORD", "password")
DBHOST=os.getenv("DBHOST", "localhost")
DBPORT=os.getenv("DBPORT", "3306")
DBNAME=os.getenv("DBNAME", "wateringdev")
DBOPTIONS=os.getenv("DBOPTIONS", "charset=utf8mb4")
DBDRIVER=os.getenv("DBDRIVER", "mysql+pymysql")

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", f"{DBDRIVER}://{DBUSER}:{DBPASSWORD}@{DBHOST}:{DBPORT}/{DBNAME}?{DBOPTIONS}")
print(f"Using database : {SQLALCHEMY_DATABASE_URL.split('/')[3]}")
SQL_ECHO = os.getenv("SQL_ECHO", "0") == "1"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")
    if "pump" not in config or "valve" not in config or "levels" not in config:
        raise ValueError("Config must contain 'pump', 'valve', and 'levels' keys")
    if not isinstance(config["levels"], list) or not all(isinstance(level, int) for level in config["levels"]):
        raise ValueError("Levels must be a list of integers")
    if len(config["levels"]) != 4:
        raise ValueError("Levels must contain exactly 4 integers")
    if not all(isinstance(config[key], int) for key in ["pump", "valve"]):
        raise ValueError("Pump and valve must be integers")
    if "watering" not in config:
        config["watering"] = {
            "low": {"threshold": 15, "morning-duration": 30, "evening-duration": 30},
            "moderate": {"threshold": 20, "morning-duration": 45, "evening-duration": 45},
            "standard": {"threshold": 25, "morning-duration": 60, "evening-duration": 60},
            "reinforced": {"threshold": 30, "morning-duration": 75, "evening-duration": 75},
            "high": {"threshold": 35, "morning-duration": 90, "evening-duration": 90}
        }
    if "coordinates" not in config:
        config["coordinates"] = {"latitude": 48.866667, "longitude": 2.333333}
    if not isinstance(config["coordinates"], dict) or "latitude" not in config["coordinates"] or "longitude" not in config["coordinates"]:
        raise ValueError("Coordinates must be a dictionary with 'latitude' and 'longitude' keys")
    if not isinstance(config["coordinates"]["latitude"], (int, float)) or not isinstance(config["coordinates"]["longitude"], (int, float)):
        raise ValueError("Latitude and longitude must be numbers")
    if not (-90 <= config["coordinates"]["latitude"] <= 90) or not (-180 <= config["coordinates"]["longitude"] <= 180):
        raise ValueError("Latitude must be between -90 and 90, and longitude must be between -180 and 180")
    # Serialize and save the config
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
        logger.debug(f"serialized config {config}")
