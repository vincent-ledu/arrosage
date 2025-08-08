import os
import time
from signal import signal, SIGINT
from sys import exit
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import uuid
import threading
from datetime import datetime
import atexit
from collections import defaultdict
import logging
from db import get_connection, get_tasks_by_status, init_db,add_task, update_status, get_task, get_all_tasks, get_tasks_summary_by_day
from config import load_config, save_config
import requests
from flask_babel import Babel, gettext as _, lazy_gettext as _l



ctlInst = None
if os.environ.get("TESTING") == "1":
  import control_fake as ctl
  ctlInst = ctl.FakeControl()
else:
  import control_gpio as ctl
  ctlInst = ctl.GPIOControl()

ctlInst.setup()
init_db()

# on s'assure que le dossier de logs existe
if not os.path.exists("/var/log/gunicorn"):
  os.makedirs("/var/log/gunicorn")

# Configuration globale du logger
logging.basicConfig(
  level=logging.DEBUG,  # DEBUG pour + de détails
  format="%(asctime)s [%(levelname)s] %(message)s",
  handlers=[
    logging.FileHandler("/var/log/gunicorn/arrosage.log"),   # Log dans un fichier
    logging.StreamHandler()                # Log dans la console aussi
  ]
)

logger = logging.getLogger(__name__)
app = Flask(__name__)

app.secret_key = os.environ.get("SESSION_SECRET_KEY", "ish2woo}ng5Ia7sooS0Seukei Vave9oneis1so1zu9Leb1ve&o ailophai0guo-th8jizeiPho4")

# Détection de la langue par l'URL ou les headers
def get_locale():
  if 'lang' in session:
    return session['lang']
  return request.accept_languages.best_match(["fr", "en"])

@app.context_processor
def inject_locale():
    return dict(get_locale=get_locale)

@app.context_processor
def inject_translations():
    return dict(
        translations={
            "low": _("Low"),
            "moderate": _("Moderate"),
            "standard": _("Standard"),
            "reinforced": _("Reinforced"),
            "high": _("High")
        })

app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

babel = Babel(app, locale_selector=get_locale)

@app.route('/change-lang/<lang_code>')
def change_language(lang_code):
    if lang_code in ['fr', 'en']:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

@app.before_request
def log_request_info():
    logger.info(f"Request received: {request.method} {request.path}")

cancel_flags = {}   # stocke les flags d’annulation : {task_id: threading.Event()}

@app.route('/')
def index():
  return render_template("index.html")

@app.route("/api/forecast")
def forecast():
  try:
    coordinates = get_coordinates()
    logger.debug(f"Coordinates: ${coordinates}")
    lat, lon = coordinates.values()
    url = (
      "https://api.open-meteo.com/v1/forecast"
      f"?latitude={lat}&longitude={lon}"
      "&daily=temperature_2m_max,precipitation_sum"
      "&timezone=Europe%2FParis"
    )
    r = requests.get(url, timeout=5)
    data = r.json()
    return jsonify({
      "dates": data["daily"]["time"],
      "temps": data["daily"]["temperature_2m_max"],
      "precipitations": data["daily"]["precipitation_sum"]
    })
  except Exception as e:
    logger.error("Error fetching forecast data: %s", e)       
    return jsonify({"error": str(e)}), 500

@app.route('/api/coordinates')
def get_coordinates():
  coordinates = load_config()["coordinates"]
  LATITIUDE = coordinates.get("latitude", 48.866667)  
  LONGITUDE = coordinates.get("longitude", 2.333333)
  return {"latitude": float(LATITIUDE), "longitude": float(LONGITUDE)}

@app.route("/api/temperature-max")
def get_temperature_max():
  try:
    coordinates = get_coordinates()
    logger.debug(f"Coordinates: ${coordinates}")
    lat, lon = coordinates.values()
    url = (
      "https://api.open-meteo.com/v1/forecast"
      f"?latitude={lat}&longitude={lon}"
      "&daily=temperature_2m_max&forecast_days=1&timezone=Europe%2FParis"
    )
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return jsonify(data["daily"]["temperature_2m_max"][0])
  except Exception as e:
    logger.error("Forecast error :", e)
    return jsonify({"error": "Error in calling open-meteo api"})

@app.route("/api/watering-type")
def classify_watering():
  temp = get_temperature_max().get_json()
  watering = load_config()["watering"]

  if temp is None:
    return "unknown"
  for watering_type, settings in watering.items():
    if temp < settings["threshold"]:
      return watering_type

@app.route('/settings/', methods=["GET", "POST"])
def settings_page():
  config = load_config()
  if request.method == "POST":
    config["pump"] = int(request.form.get("pump", 2))
    config["valve"] = int(request.form.get("valve", 3))
    config["levels"] = [
      int(request.form.get(f"level{i}", 7 + i))
      for i in range(4)
    ]
    for watering_type in config["watering"]:
      config["watering"][watering_type]["threshold"] = int(request.form.get(f"{watering_type}_threshold", 20))
      config["watering"][watering_type]["morning-duration"] = int(request.form.get(f"{watering_type}_morning-duration", 60))
      config["watering"][watering_type]["evening-duration"] = int(request.form.get(f"{watering_type}_evening-duration", 60))
    config["coordinates"] = {
      "latitude": float(request.form.get("latitude", 48.866667)),
      "longitude": float(request.form.get("longitude", 2.333333))
    }
    save_config(config)
    ctlInst.setup()
    # flash("Configuration enregistrée avec succès.")
    return redirect(url_for("settings_page"))
  return render_template("settings.html", config=config)

@app.route('/history')
def history_page():
  return render_template("history.html")

@app.route('/history_heatmap')
def history_heatmap_page():
  return render_template("history_heatmap.html")

def handler(signal_received, frame):
  # on gere un cleanup propre
  logger.warning('SIGINT or CTRL-C detected. Exiting gracefully')
  ctlInst.cleanup()
  exit(0)

def cleanup_app():
  logger.warning("GPIO Clean up app")
  ctlInst.cleanup()

def open_water_task(task_id, duration, cancel_event):
  try:
    interval = 1
    elapsed = 0

    ctlInst.openWater()
    while elapsed < duration:
      if cancel_event.is_set():
        update_status(task_id, "canceled")
        return
      if not IfWater():
        logger.warning("Not enough water to continue")
        ctlInst.closeWater()
        update_status(task_id, "canceled")
        return
      time.sleep(interval)
      elapsed += interval
    ctlInst.closeWater()
    update_status(task_id, "completed")
  except Exception as e:
      update_status(task_id, f"error: {str(e)}")


@app.route("/api/water-level")
def CheckWaterLevel():
  level = ctlInst.getLevel()
  logger.info(f"Container is at: {level}")
  return { "level": level*25 }


@app.route("/api/water-levels")
def DebugWaterLevels():
  return jsonify(ctlInst.debugWaterLevels()), 200


@app.route('/api/tasks')
def task_list():
   return jsonify(get_all_tasks())


@app.route('/api/tasks/<task_id>')
def task_status(task_id):
  task = get_task(task_id)
  if not task:
      return jsonify({"error": f"Task {task_id} not found"}), 404
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
@app.route("/api/command/open-water", methods=["GET"])
def OpenWaterDelay():

  duration = request.args.get("duration", type=int)
  if duration is None:
    logger.warning("No duration provided")
    return jsonify({"error": "Duration parameter is required"}), 400                       

  if duration <= 0 or duration > 300:
    logger.warning("Delay is to high, risk to empty container")
    return jsonify({"error": "Invalid duration"}), 400
  # Vérifie s’il existe déjà une tâche en cours
  if (get_tasks_by_status("in progress")):
    return jsonify({"error": "Watering is already in progress."}), 409
  if not IfWater():
    logger.warning("There is not enough water")
    return jsonify({"error": "Not enough water."}), 507   
  
  start_time = time.time()
  task_id = add_task(start_time, duration, "in progress")
  cancel_event = threading.Event()
  cancel_flags[task_id] = cancel_event

  # Lancement en thread
  thread = threading.Thread(target=open_water_task, args=(task_id, duration, cancel_event))
  thread.start()

  return jsonify({"task_id": task_id, "status": "in progress"}), 202

@app.route("/api/command/close-water")
def closeWaterSupply():
  ctlInst.closeWater()

  cancelled_tasks = []
  for task in get_tasks_by_status("in progress"):
    cancel_event = cancel_flags.get(task.get("id"))
    if cancel_event:
      cancel_event.set()
      update_status(task.get("id"), "canceled")
      cancelled_tasks.append(task.get("id"))
  if len(cancelled_tasks) > 0:
    return jsonify({"message": f"Task {cancelled_tasks} terminated"}), 200
  return jsonify({"error": "Water is already closed"}), 404

@app.route('/api/history')
def get_history():
  history = defaultdict(int)
  for task in get_tasks_by_status("completed"):
    day = datetime.fromtimestamp(task["start_time"]).strftime('%Y-%m-%d')
    history[day] += task.get("duration", 0)

  # Convert durations en minutes, rounded
  result = [{"date": day, "duration": round(seconds / 60, 1)} for day, seconds in sorted(history.items())]
  return jsonify(result)

@app.route('/api/history-heatmap')
def history_heatmap():
  return jsonify(get_tasks_summary_by_day())

@app.route('/health')
def health():
  try:
    ctlInst.getLevel()  # Vérifie si le contrôle fonctionne
    conn = get_connection()
    if conn is None:
      raise Exception("Database connection failed")
    conn.execute("SELECT 1")  # Teste une requête simple
    conn.close()
    return jsonify({"status": "healthy"}), 200
  except Exception as e:
    logger.error(f"Health check failed: {e}")
    return jsonify({"status": "unhealthy"}), 500

@app.route('/api/healthcheck')
def healthcheck():
  try:
    ctlInst.getLevel()  # Vérifie si le contrôle fonctionne
    conn = get_connection()
    if conn is None:
      raise Exception("Database connection failed")
    conn.execute("SELECT 1")  # Teste une requête simple
    conn.close()
    get_temperature_max()
    return jsonify({"status": "healthy"}), 200
  except Exception as e:
    logger.error(f"Health check failed: {e}")
    return jsonify({"status": "unhealthy"}), 500

if __name__ == '__main__':
  # On prévient Python d'utiliser la method handler quand un signal SIGINT est reçu
  signal(SIGINT, handler)
  #Register the function to be called on exit
  atexit.register(cleanup_app)
  app.run(host="0.0.0.0", port=3000, debug=True)