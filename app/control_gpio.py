from control_interface import Control
import RPi.GPIO as GPIO
import logging
from config import load_config
import time

logger = logging.getLogger(__name__)

class GPIOControl(Control):
  
  def __init__(self):
    self.control_state = {
      "pump": None,
      "valve": None,
      "levels": []
    }
  
  @property
  def control_state(self):
    return self._control_state
  @control_state.setter
  def control_state(self, value):
    if not isinstance(value, dict):
      raise ValueError("control_state must be a dictionary")
    self._control_state = value
  
  def setup(self):
    # Initialisation générale (mode BCM)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    config = load_config()
    self.releaseAll()

    self.control_state["pump"] = config["pump"]
    self.control_state["valve"] = config["valve"]
    self.control_state["levels"] = config["levels"]

    # Configure les sorties
    GPIO.setup(self.control_state["pump"], GPIO.OUT)
    GPIO.setup(self.control_state["valve"], GPIO.OUT)

    # Configure les capteurs de niveau en entrée avec pull-down
    for pin in self.control_state["levels"]:
      GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    logger.info("✅ GPIO initialized with:")
    logger.info(f"  Pump : GPIO {self.control_state['pump']}")
    logger.info(f"  Valve : GPIO {self.control_state['valve']}")
    logger.info(f"  Levels : {self.control_state['levels']}")

  def releaseAll(self):
    all_pins = [self.control_state["pump"], self.control_state["valve"]] + self.control_state["levels"]
    for pin in all_pins:
      if pin is not None:
        try:
          GPIO.cleanup(pin)  # free pin if it was used
        except Exception:
          pass

  def openWater(self):
    logger.info("Turning On valve")
    GPIO.output(self.control_state["valve"], GPIO.HIGH)
    time.sleep(2)
    logger.info("Turning On pump")
    GPIO.output(self.control_state["pump"], GPIO.HIGH)

  def closeWater(self):
    logger.info("Turning Off pump")
    GPIO.output(self.control_state["pump"], GPIO.LOW)
    time.sleep(2)
    logger.info("Turning Off valve")
    GPIO.output(self.control_state["valve"], GPIO.LOW)
  
  def DebugWaterLevels(self):
    water_states = {}
    for i in range(4):
      water_states[f"level_{i}"] = {
        "gpio_pin": self.control_state["levels"][i],
        "state": GPIO.input(self.control_state["levels"][i])
      }
    return water_states

  def getLevel(self):
    level = 0
    for i in range(4):
      logger.info(f"Checking level {i}")
      if GPIO.input(self.control_state["levels"][i]):
        level += 1
    return level

  def cleanup(self):
    GPIO.cleanup()
    logger.info("GPIO cleaned up successfully.")
  