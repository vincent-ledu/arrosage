import logging
from control.control_interface import Control

logger = logging.getLogger(__name__)


class FakeControl(Control):
    def __init__(self):
        self._control_state = {"pump": None, "valve": None, "levels": []}
        self._level = 4  # Default level for testing

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        logger.debug(f"Setting level to {value}")
        if not isinstance(value, int) or value < 0:
            raise ValueError("level must be a positive integer")
        self._level = value

    @property
    def control_state(self):
        return self._control_state

    @control_state.setter
    def control_state(self, value):
        if not isinstance(value, dict):
            raise ValueError("control_state must be a dictionary")
        self._control_state = value

    def releaseAll(self):
        pass

    def openWater(self):
        logger.info("FAKE: valve opened")
        logger.info("FAKE: pump started")

    def closeWater(self):
        logger.info("FAKE: pump stopped")
        logger.info("FAKE: valve closed")

    def debugWaterLevels(self):
        water_states = {}
        for i in range(4):
            water_states[f"level_{i}"] = {"gpio_pin": "fake_pin", "state": "fake_state"}
        return water_states

    def getLevel(self):
        return self.level

    def cleanup(self):
        pass

    def setup(self):
        pass
