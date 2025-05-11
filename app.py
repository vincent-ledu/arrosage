import RPi.GPIO as GPIO
import time
from signal import signal, SIGINT
from sys import exit
from flask import Flask, request
import atexit

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# Numérotation BCM (par GPIO, pas numéro de pin physique)
GPIO.setmode(GPIO.BCM)

VANNE=20
PUMP=21
WATER_EMPTY = 23
WATER_QUARTER = 24
WATER_HALF = 25
WATER_FULL = 26

WATER_LEVELS = [WATER_EMPTY, WATER_QUARTER, WATER_HALF, WATER_FULL]

# Configurer le GPIO en entrée avec pull-down externe
GPIO.setup(WATER_EMPTY, GPIO.IN)
GPIO.setup(WATER_QUARTER, GPIO.IN)
GPIO.setup(WATER_HALF, GPIO.IN)
GPIO.setup(WATER_FULL, GPIO.IN)
GPIO.setup(VANNE, GPIO.OUT)
GPIO.setup(PUMP, GPIO.OUT)

def handler(signal_received, frame):
  # on gere un cleanup propre
  print('SIGINT or CTRL-C detected. Exiting gracefully')
  GPIO.cleanup()
  exit(0)

def cleanup_app():
  GPIO.cleanup()

@app.route("/checkWaterLevel")
def CheckWaterLevel():
  if GPIO.input(WATER_FULL):
    print("Container full")
    return { "level": 100 }
  if not GPIO.input(WATER_HALF):
    print("Container on half")
    return { "level": 50 }
  if not GPIO.input(WATER_QUARTER):
    print("Container on quarter")
    return { "level": 25 }
  if GPIO.input(WATER_EMPTY):
    print("Container nearly empty")
    return { "level": 2 }
  print("Container empty")
  return { "level": 0 }

def IfWater():
  return GPIO.input(WATER_EMPTY)
   

'''
Open water for 'delay' seconds, if there is enough water
Delay must be under 300 seconds (5minutes)
'''
@app.route("/openwater")
def OpenWaterDelay(delay):
  delay = int(request.args.get('delay'))
  print("check if water")
  if not IfWater():
    print("There is not enough water")
    return   
  if delay > 300:
    print("Delay is to high, risk to empty containter")
    return
  print("Turning On VANNE")
  GPIO.output(VANNE, GPIO.HIGH)
  time.sleep(2)
  print("Turning On PUMP")
  GPIO.output(PUMP, GPIO.HIGH)
  time.sleep(delay)
  print("Turning Off VANNE & PUMP")
  GPIO.output(VANNE, GPIO.LOW)
  GPIO.output(PUMP, GPIO.LOW)

if __name__ == '__main__':
  # On prévient Python d'utiliser la method handler quand un signal SIGINT est reçu
  signal(SIGINT, handler)
  #Register the function to be called on exit
  atexit.register(cleanup_app)
  app.run(host="0.0.0.0", port=3000)