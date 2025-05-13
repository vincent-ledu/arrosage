from gpiozero import Button, LED
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
from db import get_tasks_by_status, init_db, add_task, update_status, get_task, get_all_tasks, get_tasks_summary_by_day

init_db()

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

VANNE=20
PUMP=21
WATER_EMPTY = 23
WATER_ATHIRD = 24
WATER_TWOTHIRDS = 25
WATER_FULL = 26

WATER_LEVELS = [WATER_EMPTY, WATER_ATHIRD, WATER_TWOTHIRDS, WATER_FULL]

# Configurer le GPIO en entrée avec pull-down externe
water_level_empty = Button(WATER_EMPTY)
water_level_athird = Button(WATER_ATHIRD)
water_level_twothird = Button(WATER_TWOTHIRDS)
water_level_full = Button(WATER_FULL)
vanneLed = LED(VANNE)
pumpLed = LED(PUMP)

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

def open_water_task(task_id, duration, cancel_event):
  try:
    interval = 1
    elapsed = 0

    logger.info("Turning On VANNE")
    vanneLed.on()
    time.sleep(2)
    logger.info("Turning On PUMP")
    pumpLed.on()
    while elapsed < duration:
      if cancel_event.is_set():
          update_status(task_id, "annulé")
          return
      time.sleep(interval)
      elapsed += interval
    logger.info("Turning Off VANNE & PUMP")
    vanneLed.off()
    pumpLed.off()
    update_status(task_id, "terminé")
  except Exception as e:
      update_status(task_id, f"erreur: {str(e)}")


@app.route("/api/water-level")
def CheckWaterLevel():
  if not water_level_full.is_pressed:
    logger.info("Container full")
    return { "level": 100 }
  if not water_level_twothird.is_pressed:
    logger.info("Container 2/3")
    return { "level": 66 }
  if not water_level_athird.is_pressed:
    logger.info("Container 1/3")
    return { "level": 33 }
  if not water_level_empty.is_pressed:
    logger.info("Container nearly empty")
    return { "level": 10 }
  logger.info("Container empty")
  return { "level": 0 }


@app.route("/api/water-levels")
def CheckWaterLevels():
  water_states = {}
  water_states["WATER_FULL"] = {"gpio_pin": WATER_FULL, "state": water_level_full.is_pressed}
  water_states["WATER_TWOTHIRDS"] = {"gpio_pin": WATER_TWOTHIRDS, "state": water_level_twothird.is_pressed}
  water_states["WATER_ATHIRD"] = {"gpio_pin": WATER_ATHIRD, "state": water_level_athird.is_pressed}
  water_states["WATER_EMPTY"] = {"gpio_pin": WATER_EMPTY, "state": water_level_empty.is_pressed}
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
  return not water_level_empty.is_pressed


'''
Open water for 'delay' seconds, if there is enough water
Delay must be under 300 seconds (5minutes)
'''
@app.route("/api/open-water")
def OpenWaterDelay():
  # Vérifie s’il existe déjà une tâche en cours
  if (get_tasks_by_status("en cours")):
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
  add_task(task_id, start_time, duration, "en cours")
  # Lancement en thread
  thread = threading.Thread(target=open_water_task, args=(task_id, duration, cancel_event))
  thread.start()

  return jsonify({"task_id": task_id, "status": "en cours"}), 202

@app.route("/api/close-water")
def closeWaterSupply():
  logger.info("Turning Off VANNE & PUMP")
  vanneLed.off()
  pumpLed.off()

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


if __name__ == '__main__':
  app.run(host="0.0.0.0", port=3000, debug=True)