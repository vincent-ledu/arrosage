import RPi.GPIO as GPIO
import time
from signal import signal, SIGINT
from sys import exit
from flask import Flask, request, render_template, jsonify
import uuid
import threading
from datetime import datetime
import atexit
from collections import defaultdict
import logging

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

# Numérotation BCM (par GPIO, pas numéro de pin physique)
GPIO.setmode(GPIO.BCM)

VANNE=20
PUMP=21
WATER_EMPTY = 23
WATER_ATHIRD = 24
WATER_TWOTHIRDS = 25
WATER_FULL = 26

WATER_LEVELS = [WATER_EMPTY, WATER_ATHIRD, WATER_TWOTHIRDS, WATER_FULL]

# Configurer le GPIO en entrée avec pull-down externe
GPIO.setup(WATER_EMPTY, GPIO.IN)
GPIO.setup(WATER_ATHIRD, GPIO.IN)
GPIO.setup(WATER_TWOTHIRDS, GPIO.IN)
GPIO.setup(WATER_FULL, GPIO.IN)
GPIO.setup(VANNE, GPIO.OUT)
GPIO.setup(PUMP, GPIO.OUT)

tasks = {}  # Dictionnaire pour stocker l’état des tâches
cancel_flags = {}   # stocke les flags d’annulation : {task_id: threading.Event()}

@app.route('/')
def index():
  return render_template('index.html')
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

    logger.info("Turning On VANNE")
    GPIO.output(VANNE, GPIO.HIGH)
    time.sleep(2)
    logger.info("Turning On PUMP")
    GPIO.output(PUMP, GPIO.HIGH)
    while elapsed < duration:
      if cancel_event.is_set():
          tasks[task_id]["status"] = "annulé"
          return
      time.sleep(interval)
      elapsed += interval
    logger.info("Turning Off VANNE & PUMP")
    GPIO.output(VANNE, GPIO.LOW)
    GPIO.output(PUMP, GPIO.LOW)
    tasks[task_id]["status"] = "terminée"
  except Exception as e:
      tasks[task_id]["status"] = f"erreur: {str(e)}"


@app.route("/api/water-level")
def CheckWaterLevel():
  if not GPIO.input(WATER_FULL):
    logger.info("Container full")
    return { "level": 100 }
  if not GPIO.input(WATER_TWOTHIRDS):
    logger.info("Container on half")
    return { "level": 66 }
  if not GPIO.input(WATER_ATHIRD):
    logger.info("Container on quarter")
    return { "level": 33 }
  if not GPIO.input(WATER_EMPTY):
    logger.info("Container nearly empty")
    return { "level": 10 }
  logger.info("Container empty")
  return { "level": 0 }


@app.route("/api/water-levels")
def CheckWaterLevels():
  water_states = {}
  water_states["WATER_FULL"] = {"gpio_pin": WATER_FULL, "state": GPIO.input(WATER_FULL)}
  water_states["WATER_TWOTHIRDS"] = {"gpio_pin": WATER_TWOTHIRDS, "state": GPIO.input(WATER_TWOTHIRDS)}
  water_states["WATER_ATHIRD"] = {"gpio_pin": WATER_ATHIRD, "state": GPIO.input(WATER_ATHIRD)}
  water_states["WATER_EMPTY"] = {"gpio_pin": WATER_EMPTY, "state": GPIO.input(WATER_EMPTY)}
  return jsonify(water_states), 200


@app.route('/api/tasks')
def task_list():
   return jsonify(tasks)


@app.route('/api/task-status/<task_id>')
def task_status(task_id):
  task = tasks.get(task_id)
  if not task:
      return jsonify({"error": "Tâche introuvable"}), 404
  logger.debug(task)
  return jsonify({
      "status": task["status"],
      "start_time": task["start_time"],
      "duration": task["duration"]
  })

def IfWater():
  return not GPIO.input(WATER_EMPTY)


'''
Open water for 'delay' seconds, if there is enough water
Delay must be under 300 seconds (5minutes)
'''
@app.route("/api/open-water")
def OpenWaterDelay():
  # Vérifie s’il existe déjà une tâche en cours
  if any(status == "en cours" for status in tasks.values()):
    return jsonify({"error": "Une vanne est déjà ouverte. Attendez qu'elle se referme."}), 409

  duration = int(request.args.get("duration", "0"))
                              
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
  tasks[task_id] = {
    "status": "en cours",
    "start_time": start_time,
    "duration": duration
  }
  # Lancement en thread
  thread = threading.Thread(target=open_water_task, args=(task_id, duration, cancel_event))
  thread.start()

  return jsonify({"task_id": task_id, "status": "en cours"}), 202

@app.route("/api/close-water")
def closeWaterSupply():
  logger.info("Turning Off VANNE & PUMP")
  GPIO.output(VANNE, GPIO.LOW)
  GPIO.output(PUMP, GPIO.LOW)
  
  for task_id, task in tasks.items():
    if task["status"] == "en cours":
      cancel_event = cancel_flags.get(task_id)
      if cancel_event:
        cancel_event.set()
        task["status"] = "annulé"
        return jsonify({"message": f"Tâche {task_id} arrêtée"}), 200
  return jsonify({"message": "Aucune tâche en cours à arrêter"}), 400

@app.route('/api/history')
def get_history():
  history = defaultdict(int)
  for task in tasks.values():
    logger.debug(task)
    if task.get("status") == "terminée":
      day = datetime.fromtimestamp(task["start_time"]).strftime('%Y-%m-%d')
      history[day] += task.get("duration", 0)

  # Convert durations en minutes, rounded
  result = [{"date": day, "duration": round(seconds / 60, 1)} for day, seconds in sorted(history.items())]
  return jsonify(result)

@app.route('/api/history-heatmap')
def history_heatmap():
  from collections import defaultdict

  history = defaultdict(int)
  for task in tasks.values():
    if task.get("status") == "terminée":
      ts = int(task["start_time"])
      history[ts - ts % 86400] += task.get("duration", 0)  # arrondi à minuit

  # Format attendu par Cal-Heatmap : {timestamp (sec): valeur numérique}
  return jsonify(history)


if __name__ == '__main__':
  # On prévient Python d'utiliser la method handler quand un signal SIGINT est reçu
  signal(SIGINT, handler)
  #Register the function to be called on exit
  atexit.register(cleanup_app)
  app.run(host="0.0.0.0", port=3000, debug=True)