import os
import time
from signal import signal, SIGINT
from sys import exit
from flask import Flask, flash, request, render_template, jsonify, redirect, url_for, session
import threading
from datetime import date, timedelta, datetime
import atexit
import logging
import requests
from flask_babel import Babel, gettext as _, lazy_gettext as _l

import config.config as local_config
from db import db_tasks, db_weather_data, db_forecast_data

from services import weather
from utils.serializer import task_to_dict
from routes.history_series import bp as history_series_bp

ENVIRONMENT = os.environ.get("FLASK_ENV", "production")
PORT = int(os.environ.get("PORT", 3000))
HOST = os.environ.get("HOST", "0.0.0.0")
TTL = timedelta(minutes=30)

ctlInst = None
if ENVIRONMENT in ["development", "test"]:
  from control.control_fake import FakeControl
  ctlInst = FakeControl()
else:
  from control.control_gpio import GPIOControl
  ctlInst = GPIOControl()

ctlInst.setup()

# on s'assure que le dossier de logs existe
if not os.path.exists("/var/log/gunicorn"):
  os.makedirs("/var/log/gunicorn")

# Configuration globale du logger
logging.basicConfig(
  level=logging.DEBUG if ENVIRONMENT == "development" else logging.info,
  format="%(asctime)s [%(levelname)s] %(message)s",
  handlers=[
    logging.FileHandler("/var/log/gunicorn/arrosage.log"),   # Log dans un fichier
    logging.StreamHandler()                # Log dans la console aussi
  ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.secret_key = os.environ.get("SESSION_SECRET_KEY", "ish2woo}ng5Ia7sooS0Seukei Vave9oneis1so1zu9Leb1ve&o ailophai0guo-th8jizeiPho4")

app.register_blueprint(history_series_bp)


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

app.config["VERSION"] = local_config.VERSION

@app.context_processor
def inject_version():
    return dict(version=app.config["VERSION"])

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

class UserVisibleError(Exception):
    pass

@app.errorhandler(UserVisibleError)
def handle_user_visible_error(e, page):
    flash(str(e), "error")
    # Redirigez vers une page pertinente
    return redirect(url_for(page))

@app.route('/')
def index():
  return render_template("index.html")

@app.route("/api/forecast")
def forecast():
  try:
    fd = db_forecast_data.get_forecast()
    if len(fd) >= 5 and datetime.now() < (datetime.strptime(fd[0]["updated_at"], "%Y-%m-%d %H:%M:%S") + TTL):
      logger.debug("return result from db")
      return jsonify(fd[:5]), 200
  
    logger.debug("fetch forecast from open-meteo")
    coordinates = get_coordinates()
    lat, lon = coordinates.values()
    data = weather.fetch_open_meteo(lat, lon)
    partday_data = weather.aggregate_by_partday(data)
    db_forecast_data.add_forecast_data(partday_data) 
    return jsonify(partday_data[:5]), 201
  except Exception as e:
    logger.error("Error fetching forecast data: %s", e)
    logger.exception(e)
    return jsonify({"error": str(e), 
                    "flash": {
                      "message": "_('Error fetching weather data. Please try again later.')", 
                      "category": "warning"
                      }
                      }), 500

@app.route('/api/coordinates')
def get_coordinates():
  coordinates = local_config.load_config()["coordinates"]
  LATITIUDE = coordinates.get("latitude", 48.866667)  
  LONGITUDE = coordinates.get("longitude", 2.333333)
  return {"latitude": float(LATITIUDE), "longitude": float(LONGITUDE)}


@app.route("/api/temperature-max")
def get_temperature_max():
  try:
    data = get_minmax_temperature_precip()
    if isinstance(data, tuple):
      data, status_code = data
      if status_code != 200 and status_code != 201:
        logger.error(f"Error fetching temperature max: {data}")
        return data, status_code
    max_temp = data.get_json().get("temperature_2m_max")
    if max_temp is None:
      raise ValueError("Max temperature not found in forecast data")
    return jsonify(max_temp), 200
  except Exception as e:
    logger.error("Forecast error :%s", e)
    return jsonify({"error": "Error in calling open-meteo api", "flash": {
                      "message": "_('Error fetching weather data. Please try again later.')", 
                      "category": "warning"
                      }
                      }), 500
  

def is_fresh(data) -> bool:
  if not data:
      return False
  return datetime.now() < (data.updated_at + TTL)

@app.route("/api/forecast-minmax-precip")  
def get_minmax_temperature_precip():
  try:
    fs = db_weather_data.get_weather_data_by_date(date.today())
    logger.debug(f"fs: {fs}")
    if fs is None or not is_fresh(fs):
      logger.info("No forecast data in DB or not fresh, fetching from API")
      coordinates = get_coordinates()
      lat, lon = coordinates.values()
      url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=1&timezone=Europe%2FParis"
      )
      resp = requests.get(url, timeout=5)
      resp.raise_for_status()
      data = resp.json()
      db_weather_data.add_weather_data(date.today(),
                        data["daily"]["temperature_2m_min"][0],
                        data["daily"]["temperature_2m_max"][0],
                        data["daily"]["precipitation_sum"][0])
      return jsonify({
        "temperature_2m_max": data["daily"]["temperature_2m_max"][0],
        "temperature_2m_min": data["daily"]["temperature_2m_min"][0],
        "precipitation_sum": data["daily"]["precipitation_sum"][0]}), 201
    logger.info("Forecast data found in DB")
    logger.debug(f"Forecast data from DB: {fs}")
    return jsonify({
      "temperature_2m_max": fs.max_temp,
      "temperature_2m_min": fs.min_temp,
      "precipitation_sum": fs.precipitation
    }), 200
  except Exception as e:
    logger.error("Forecast error : %s", e)
    logger.exception(e)
    return jsonify({"error": "Error in calling open-meteo api", 
                    "flash": {
                      "message": "_('Error fetching weather data. Please try again later.')", 
                      "category": "warning"
                      }
                      }), 500

@app.route("/api/watering-type")
def classify_watering():
  temp = request.args.get("temp", type=float)
  if temp is None:
    temp_data, status_code = get_temperature_max()
    logger.debug(f"Temperature max data: {temp_data.get_json()}")
    if status_code != 200:
      return jsonify({"error": "Failed to fetch temperature"}), 500
    temp_json = temp_data.get_json()
    temp = temp_json if isinstance(temp_json, (int, float)) else temp_json
    if isinstance(temp, dict) and "error" in temp:
      return jsonify({"error": "Failed to fetch temperature"}), 500
  watering = local_config.load_config()["watering"]

  if temp is None:
    return "unknown", 200

  for watering_type, settings in watering.items():
    if temp < settings["threshold"]:
      return watering_type, 200

  # If no type matched, return the highest type
  highest_type = max(watering.items(), key=lambda x: x[1]["threshold"])[0]
  return highest_type, 200

@app.route('/settings/', methods=["GET", "POST"])
def settings_page():
  config = local_config.load_config()
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
    config["enabled_months"] = [int(m) for m in request.form.getlist("enabled_months")]
    local_config.save_config(config)
    ctlInst.setup()
    flash(_('Settings saved successfully.'), "success")
    return redirect(url_for("settings_page"))
  return render_template("settings.html", config=config)

@app.route('/history')
def history_page():
  return render_template("history.html")

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
        db_tasks.update_status(task_id, "canceled")
        return
      if not IfWater():
        logger.warning("Not enough water to continue")
        ctlInst.closeWater()
        db_tasks.update_status(task_id, "canceled")
        return
      time.sleep(interval)
      elapsed += interval
    ctlInst.closeWater()
    db_tasks.update_status(task_id, "completed")
  except Exception as e:
      db_tasks.update_status(task_id, f"error: {str(e)}")


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
   return jsonify([task_to_dict(t) for t in db_tasks.get_all_tasks()]), 200


@app.route('/api/tasks/<task_id>')
def get_task_by_id(task_id):
  task = db_tasks.get_task(task_id)
  if not task:
      return jsonify({"error": f"Task {task_id} not found"}), 404
  return jsonify(task_to_dict(task)), 200

@app.route('/api/task')
def current_task():
  tasks = db_tasks.get_tasks_by_status("in progress")
  if not tasks:
      return jsonify({"task_id": None}), 404
  task = tasks[0]
  return jsonify({"task_id": task.id}), 200

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
    return jsonify({"error": "Duration parameter is required", 
                   "flash": {
                      "message": f"{_('Duration parameter is required')}", 
                      "category": "error"
                      }}
                      ), 400                       

  if duration <= 0 or duration > 300:
    logger.warning("Delay is to high, risk to empty container")
    return jsonify({"error": "Invalid duration", 
                    "flash": {
                      "message": f"{_('Value must be between 0 and 300')}", 
                      "category": "error"
                      }
                      }), 400
  # Vérifie s’il existe déjà une tâche en cours
  if (db_tasks.get_tasks_by_status("in progress")):
    logger.warning("There is already a watering in progress")
    return jsonify({"error": "Watering is already in progress.", 
                    "flash": {
                      "message": f"{_('Watering is already in progress.')}",
                      "category": "error"
                      }}), 409
  if not IfWater():
    logger.warning("There is not enough water")
    return jsonify({"error": "Not enough water.", 
                    "flash": {
                      "message": f"{_('Not enough water to start watering.')}", 
                      "category": "error"
                      }}), 507
  
  weather_data, status_code = get_minmax_temperature_precip()
  logger.debug(f"Weather data for watering check: {weather_data.get_json()}")
  if status_code != 200 and status_code != 201:
    logger.error(f"Error fetching temperature max: {weather_data}")
    return weather_data, status_code
  min_temp = weather_data.get_json().get("temperature_2m_min")
  if min_temp is None:
    logger.error("Min temperature not found in forecast data")
    return jsonify({"error": "Min temperature not found in forecast data"}), 500
  if min_temp < 5:
    logger.warning("Temperature is too low to water")
    return jsonify({"error": "Temperature is too low to water.", 
                    "flash": {
                      "message": f"{_('Temperature is too low to water.')}", 
                      "category": "warning"
                      }}), 400
  current_month = date.today().month
  enabled_months = local_config.load_config().get("enabled_months", list(range(1,13)))
  if current_month not in enabled_months:
    logger.warning("Watering is disabled for the current month")
    return jsonify({"error": "Watering is disabled for the current month.", 
                    "flash": {
                      "message": f"{_('Watering is disabled for the current month.')}", 
                      "category": "warning"
                      }}), 400
  task_id = db_tasks.add_task(duration, "in progress")
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
  for task in db_tasks.get_tasks_by_status("in progress"):
    cancel_event = cancel_flags.get(task.id)
    if cancel_event:
      cancel_event.set()
      db_tasks.update_status(task.id, "canceled")
      cancelled_tasks.append(task.id)
  if len(cancelled_tasks) > 0:
    return jsonify({"message": f"Task {cancelled_tasks} terminated", 
                    "flash": {
                      "message": "_('Watering task terminated.')", 
                      "category": "success"
                      }}), 200
  return jsonify({"error": "Water is already closed", 
                    "flash": {
                      "message": "_('Water is already closed.')", 
                      "category": "warning"
                      }}), 404

@app.route('/health')
@app.route('/healthz')
@app.route('/healthcheck')
@app.route('/api/healthcheck')
def health():
  try:
    ctlInst.getLevel()  # Vérifie si le contrôle fonctionne
    conn = db_tasks.get_connection()
    if conn is None:
      raise Exception("Database connection failed")
    conn.close()
    return jsonify({"status": "healthy"}), 200
  except Exception as e:
    logger.error(f"Health check failed: {e}")
    return jsonify({"status": "unhealthy"}), 500


if __name__ == '__main__':
  # import random
  # for i in range(0, 5):
  #   logger.debug(db_forecast_data.add_forecast_data(date.today() + timedelta(days=i), float(random.randint(5,13) * 1.0), float(random.randint(23,25) * 1.0), float(random.randint(0, 20) * 1.0)))
  # for fd in db_forecast_data.get_forecast():
  #   logger.debug(fd.date  )
  signal(SIGINT, handler)
  atexit.register(cleanup_app)
  logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
  app.run(host="0.0.0.0", port=3000, debug=True)