import RPi.GPIO as GPIO
import time

# Numérotation BCM (par GPIO, pas numéro de pin physique)
GPIO.setmode(GPIO.BCM)

# GPIO à utiliser (par exemple GPIO17)
WATER_LOW = 23

# Configurer le GPIO en entrée avec pull-down externe
GPIO.setup(WATER_LOW, GPIO.IN)

try:
    print("Surveillance du circuit (CTRL+C pour quitter)...")
    while True:
        if GPIO.input(WATER_LOW):
            print("Niveau d'eau bas - ok")
        else:
            print("YA PLUS D'EAU")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nArrêt du programme.")

finally:
    GPIO.cleanup()
