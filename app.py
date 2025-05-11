import RPi.GPIO as GPIO
from time import strftime, time
from signal import signal, SIGINT
from sys import exit
from flask import Flask, request, render_template, jsonify
import uuid
import threading
from datetime import datetime
import atexit

app = Flask(__name__)


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

def handler(signal_received, frame):
  # on gere un cleanup propre
  print('SIGINT or CTRL-C detected. Exiting gracefully')
  print("GPIO Clean up")
  GPIO.cleanup()
  exit(0)

def cleanup_app():
  print("GPIO Clean up")
  GPIO.cleanup()


def open_valve_task(task_id, duration):
    try:
      print("Turning On VANNE")
      GPIO.output(VANNE, GPIO.HIGH)
      time.sleep(2)
      print("Turning On PUMP")
      GPIO.output(PUMP, GPIO.HIGH)
      time.sleep(duration)
      print("Turning Off VANNE & PUMP")
      GPIO.output(VANNE, GPIO.LOW)
      GPIO.output(PUMP, GPIO.LOW)
      tasks[task_id] = "terminée"
    except Exception as e:
        tasks[task_id] = f"erreur: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/api/checkWaterLevel")
def CheckWaterLevel():
  if GPIO.input(WATER_FULL):
    print("Container full")
    return { "level": 100 }
  if not GPIO.input(WATER_TWOTHIRDS):
    print("Container on half")
    return { "level": 66 }
  if not GPIO.input(WATER_ATHIRD):
    print("Container on quarter")
    return { "level": 33 }
  if GPIO.input(WATER_EMPTY):
    print("Container nearly empty")
    return { "level": 10 }
  print("Container empty")
  return { "level": 0 }


@app.route('/api/task-status')
def task_list():
   return jsonify(tasks)


@app.route('/api/task-status/<task_id>')
def task_status(task_id):
    status = tasks.get(task_id)
    if status is None:
        return jsonify({"error": "Tâche inconnue"}), 404
    return jsonify({"task_id": task_id, "status": status})

def IfWater():
  return GPIO.input(WATER_EMPTY)


'''
Open water for 'delay' seconds, if there is enough water
Delay must be under 300 seconds (5minutes)
'''
@app.route("/api/openwater")
def OpenWaterDelay():
  # Vérifie s’il existe déjà une tâche en cours
  if any(status == "en cours" for status in tasks.values()):
      return jsonify({"error": "Une vanne est déjà ouverte. Attendez qu'elle se referme."}), 409

  duration = int(request.args.get("duration", "10"))
  print(duration)
                              
  print("check if water")
  if not IfWater():
    print("There is not enough water")
    return   
  if duration > 300:
    print("Delay is to high, risk to empty containter")
    return
  
  now = datetime.now()
  
  task_id = str(uuid.uuid4())
  tasks[task_id] = "Ouverture vanne lancée à {date} pour {duration} secondes.".format(date=strftime("%H:%M:%S", now), duration=duration)

  # Lancement en thread
  thread = threading.Thread(target=open_valve_task, args=(task_id, duration))
  thread.start()

  return jsonify({"task_id": task_id, "status": "en cours"}), 202


if __name__ == '__main__':
  # On prévient Python d'utiliser la method handler quand un signal SIGINT est reçu
  signal(SIGINT, handler)
  #Register the function to be called on exit
  atexit.register(cleanup_app)
  app.run(host="0.0.0.0", port=3000)