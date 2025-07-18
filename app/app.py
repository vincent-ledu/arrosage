import os
import RPi.GPIO as GPIO
import time
from signal import signal, SIGINT
from sys import exit
from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
import uuid
import threading
from datetime import datetime
import atexit
from collections import defaultdict
import logging
from db import get_tasks_by_status, init_db, init_settings, add_task, update_status, get_task, get_all_tasks, get_tasks_summary_by_day, get_setting, set_setting
from config import load_config, save_config
from gpio_control import setup_gpio, gpio_state
import requests

setup_gpio()
init_db()
init_settings()

# Configuration globale du logger
logging.basicConfig(
  level=logging.DEBUG,  # DEBUG pour + de détails
  format="%(asctime)s [%(levelname)s] %(message)s",
  handlers=[
    logging.FileHandler("arrosage.log"),   # Log dans un fichier
    logging.StreamHandler()                # Log dans la console aussi
  ]
)

logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.before_request
def log_request_info():
    logger.info(f"Requête reçue: {request.method} {request.path}")

cancel_flags = {}   # stocke les flags d’annulation : {task_id: threading.Event()}

@app.route('/')
def index():
  return render_template("index.html")

def get_coordinates():
  lat = os.getenv("LATITUDE")
  lon = os.getenv("LONGITUDE")
  if not lat or not lon:
    return {"error": "LATITUDE or LONGITUDE not set"}
  return {"latitude": float(lat), "longitude": float(lon)}

@app.route("/api/temperature-max")
def get_temperature_max():
  try:
    coordinates = get_coordinates()
    logger.info(f"coordinates: ${coordinates}")
    lat, lon = coordinates.values()
    url = (
      "https://api.open-meteo.com/v1/forecast"
      f"?latitude={lat}&longitude={lon}"
      "&daily=temperature_2m_max&forecast_days=1&timezone=Europe/Paris"
    )
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return jsonify(data["daily"]["temperature_2m_max"][0])
  except Exception as e:
    logger.error("Erreur météo :", e)
    return jsonify({"error": "Error in calling open-meteo api"})

@app.route("/api/watering-type")
def classify_watering():
  temp = request.args.get("temp", type=float)
  if temp is None:
    return "unknown"
  if temp < 15:
    return "low"
  elif temp < 22:
    return "moderate"
  elif temp < 27:
    return "standard"
  elif temp < 32:
    return "reinforced"
  else:
    return "high"


@app.route('/config', methods=["GET", "POST"])
def config_page():
  default_duration = get_setting("default_duration", default=60)
  config = load_config()
  if request.method == "POST":
    config["pump"] = int(request.form.get("pump", 2))
    config["valve"] = int(request.form.get("valve", 3))
    config["levels"] = [
      int(request.form.get(f"level{i}", 7 + i))
      for i in range(4)
    ]
    save_config(config)
    setup_gpio()
    # flash("Configuration enregistrée avec succès.")
    return redirect(url_for("config_page"))
  return render_template("config.html", config=config, default_duration=default_duration)

@app.route('/history')
def history_page():
  return render_template("history.html")

@app.route('/history_heatmap')
def history_heatmap_page():
  return render_template("history_heatmap.html")

def handler(signal_received, frame):
  # on gere un cleanup propre
  logger.warning('SIGINT or CTRL-C detected. Exiting gracefully')
  GPIO.cleanup()
  exit(0)

def cleanup_app():
  logger.warning("GPIO Clean up app")
  GPIO.cleanup()

def open_water_task(task_id, duration, cancel_event):
  try:
    interval = 1
    elapsed = 0

    logger.info("Turning On valve")
    GPIO.output(gpio_state["valve"], GPIO.HIGH)
    time.sleep(2)
    logger.info("Turning On pump")
    GPIO.output(gpio_state["pump"], GPIO.HIGH)
    while elapsed < duration:
      if cancel_event.is_set():
        update_status(task_id, "annulé")
        return
      if not IfWater():
        GPIO.output(gpio_state["pump"], GPIO.LOW)
        time.sleep(2)
        GPIO.output(gpio_state["valve"], GPIO.LOW)
        update_status(task_id, "réservoir vide")
        return
      time.sleep(interval)
      elapsed += interval
    logger.info("Turning Off valve & pump")
    GPIO.output(gpio_state["pump"], GPIO.LOW)
    time.sleep(2)
    GPIO.output(gpio_state["valve"], GPIO.LOW)
    update_status(task_id, "terminé")
  except Exception as e:
      update_status(task_id, f"erreur: {str(e)}")


@app.route("/api/water-level")
def CheckWaterLevel():
  level = 0
  for i in range(4):
    logger.info(f"Checking level {i}")
    if GPIO.input(gpio_state["levels"][i]):
      level += 1
  logger.info(f"Container is at: {level}")
  return { "level": level*25 }


@app.route("/api/water-levels")
def DebugkWaterLevels():
  water_states = {}
  water_states["levels 3"] = {"gpio_pin": gpio_state["levels"][3], "state": GPIO.input(gpio_state["levels"][3])}
  water_states["levels 2"] = {"gpio_pin": gpio_state["levels"][2], "state": GPIO.input(gpio_state["levels"][2])}
  water_states["levels 1"] = {"gpio_pin": gpio_state["levels"][1], "state": GPIO.input(gpio_state["levels"][1])}
  water_states["levels 0"] = {"gpio_pin": gpio_state["levels"][0], "state": GPIO.input(gpio_state["levels"][0])}
  return jsonify(water_states), 200


@app.route('/api/tasks')
def task_list():
   return jsonify(get_all_tasks())


@app.route('/api/task-status/<task_id>')
def task_status(task_id):
  task = get_task(task_id)
  if not task:
      return jsonify({"error": "Tâche introuvable"}), 404
  logger.debug(task)
  return jsonify({
      "status": task["status"],
      "start_time": task["start_time"],
      "duration": task["duration"]
  })

def IfWater():
  return CheckWaterLevel()["level"] > 0


'''
Open water for 'delay' seconds, if there is enough water
Delay must be under 300 seconds (5minutes)
'''
@app.route("/api/command/open-water")
def OpenWaterDelay():
  # Vérifie s’il existe déjà une tâche en cours
  if (get_tasks_by_status("en cours")):
    return jsonify({"error": "Une vanne est déjà ouverte. Attendez qu'elle se referme."}), 409

  duration = request.args.get("duration", type=int)
  if duration is None:
    duration = get_setting("default_duration", default=60)                            
  logger.debug("check if water")
  if not IfWater():
    logger.warning("There is not enough water")
    return jsonify({"error": "Il n'y a pas assez d'eau."}), 507   
  if duration <= 0 or duration > 300:
    logger.warning("Delay is to high, risk to empty container")
    return jsonify({"error": "Durée invalide"}), 400
  
  task_id = str(uuid.uuid4())
  cancel_event = threading.Event()
  cancel_flags[task_id] = cancel_event

  start_time = time.time()
  add_task(task_id, start_time, duration, "en cours")
  # Lancement en thread
  thread = threading.Thread(target=open_water_task, args=(task_id, duration, cancel_event))
  thread.start()

  return jsonify({"task_id": task_id, "status": "en cours"}), 202

@app.route("/api/command/close-water")
def closeWaterSupply():
  logger.info("Turning Off valve & pump")
  GPIO.output(gpio_state["pump"], GPIO.LOW)
  time.sleep(2)
  GPIO.output(gpio_state["valve"], GPIO.LOW)
  
  cancelled_tasks = []
  for task in get_tasks_by_status("en cours"):
    logger.debug(f"task to cancel: {task}")
    cancel_event = cancel_flags.get(task.get("id"))
    if cancel_event:
      cancel_event.set()
      update_status(task.get("id"), "annulé")
      cancelled_tasks.append(task.get("id"))
  if len(cancelled_tasks) > 0:
    return jsonify({"message": f"Tâche {cancelled_tasks} arrêtée"}), 200
  return jsonify({"message": "Aucune tâche en cours à arrêter"}), 400

@app.route('/api/history')
def get_history():
  history = defaultdict(int)
  for task in get_tasks_by_status("terminé"):
    day = datetime.fromtimestamp(task["start_time"]).strftime('%Y-%m-%d')
    history[day] += task.get("duration", 0)

  # Convert durations en minutes, rounded
  result = [{"date": day, "duration": round(seconds / 60, 1)} for day, seconds in sorted(history.items())]
  return jsonify(result)

@app.route('/api/history-heatmap')
def history_heatmap():
  return jsonify(get_tasks_summary_by_day())

@app.route("/config/set-default-duration", methods=["POST"])
def set_default_duration():
    value = request.form.get("default_duration", type=int)
    if value and value > 0:
        set_setting("default_duration", value)
    return redirect(url_for("config_page"))


if __name__ == '__main__':
  # On prévient Python d'utiliser la method handler quand un signal SIGINT est reçu
  signal(SIGINT, handler)
  #Register the function to be called on exit
  atexit.register(cleanup_app)
  app.run(host="0.0.0.0", port=3000, debug=True)