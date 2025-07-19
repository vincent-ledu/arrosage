# gpio_control.py
import RPi.GPIO as GPIO
from config import load_config

# État courant
gpio_state = {
    "pump": None,
    "valve": None,
    "levels": []
}

# Initialisation générale (mode BCM)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def release_all():
    all_pins = [gpio_state["pump"], gpio_state["valve"]] + gpio_state["levels"]
    for pin in all_pins:
        if pin is not None:
            try:
                GPIO.cleanup(pin)  # libère la broche spécifiquement
            except Exception:
                pass

def setup_gpio():
    config = load_config()
    release_all()

    gpio_state["pump"] = config["pump"]
    gpio_state["valve"] = config["valve"]
    gpio_state["levels"] = config["levels"]

    # Configure les sorties
    GPIO.setup(gpio_state["pump"], GPIO.OUT)
    GPIO.setup(gpio_state["valve"], GPIO.OUT)

    # Configure les capteurs de niveau en entrée avec pull-down
    for pin in gpio_state["levels"]:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    print("✅ GPIO initialisé avec :")
    print(f"  Pompe : GPIO {gpio_state['pump']}")
    print(f"  Vanne : GPIO {gpio_state['valve']}")
    print(f"  Niveaux : {gpio_state['levels']}")
