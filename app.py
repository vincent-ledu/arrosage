import RPi.GPIO as GPIO
import time
from signal import signal, SIGINT
from sys import exit

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



def CheckWaterLevel():
  if GPIO.input(WATER_EMPTY):
    print("Niveau d'eau bas - ok")
  else:
    print("YA PLUS D'EAU")


def IfWater():
  return GPIO.input(WATER_EMPTY)
   

'''
Open water for 'delay' seconds, if there is enough water
Delay must be under 300 seconds (5minutes)
'''
def OpenWaterDelay(delay):
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
