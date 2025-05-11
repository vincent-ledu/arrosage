import RPi.GPIO as gpio
import time
from signal import signal, SIGINT
from sys import exit

VANNE=20
PUMP=21

def handler(signal_received, frame):
    # on gere un cleanup propre
    print('')
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    gpio.output(VANNE, gpio.HIGH)
    gpio.output(PUMP, gpio.HIGH)
    gpio.cleanup()
    exit(0)

def main():
    # on passe en mode BMC qui veut dire que nous allons utiliser directement
    # le numero GPIO plutot que la position physique sur la carte
    gpio.setmode(gpio.BCM)

    # defini le port GPIO 4 comme etant une sortie output
    gpio.setup(VANNE, gpio.OUT)
    gpio.setup(PUMP, gpio.OUT)

    # Mise a 1 pendant 2 secondes puis 0 pendant 2 seconde
    while True:
        print("Turning On VANNE")
        gpio.output(VANNE, gpio.HIGH)
        time.sleep(2)
        print("Turning On PUMP")
        gpio.output(PUMP, gpio.HIGH)
        time.sleep(2)
        print("Turning Off VANNE & PUMP")
        gpio.output(VANNE, gpio.LOW)
        gpio.output(PUMP, gpio.LOW)
        time.sleep(2)


if __name__ == '__main__':
    # On prévient Python d'utiliser la method handler quand un signal SIGINT est reçu
    signal(SIGINT, handler)
    main()
