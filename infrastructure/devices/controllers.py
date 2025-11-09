from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime

from domain.watering.entities import TankLevelSnapshot
from domain.watering.ports import DeviceController, TankLevelSensor


def _resolve_control_impl():
    base_control = importlib.import_module("app.control")
    sys.modules.setdefault("control", base_control)
    sys.modules.setdefault(
        "control.control_interface",
        importlib.import_module("app.control.control_interface"),
    )

    environment = os.environ.get("FLASK_ENV", "production")
    if environment in {"development", "test"}:
        fake_module = importlib.import_module("app.control.control_fake")
        sys.modules.setdefault("control.control_fake", fake_module)

        FakeControl = getattr(fake_module, "FakeControl")

        return FakeControl

    try:  # pragma: no cover - hardware access
        gpio_module = importlib.import_module("app.control.control_gpio")
        sys.modules.setdefault("control.control_gpio", gpio_module)

        GPIOControl = getattr(gpio_module, "GPIOControl")

        return GPIOControl
    except (ModuleNotFoundError, RuntimeError):
        fake_module = importlib.import_module("app.control.control_fake")
        sys.modules.setdefault("control.control_fake", fake_module)

        FakeControl = getattr(fake_module, "FakeControl")

        return FakeControl


ControlImpl = _resolve_control_impl()


class DeviceControllerAdapter(DeviceController):
    def __init__(self) -> None:
        self._control = ControlImpl()

    def setup(self) -> None:
        self._control.setup()

    def open_water(self) -> None:
        self._control.openWater()

    def close_water(self) -> None:
        self._control.closeWater()

    def get_level(self) -> float:
        return float(self.getLevel())

    # Compatibilité ascendante : certains tests patchent getLevel directement
    def getLevel(self) -> float:  # pragma: no cover - shim
        return float(self._control.getLevel())

    def debug_water_levels(self):
        return self._control.debugWaterLevels()

    def cleanup(self) -> None:
        self._control.cleanup()


class DeviceTankLevelSensor(TankLevelSensor):
    def __init__(self, controller: DeviceController) -> None:
        self._controller = controller

    def snapshot(self) -> TankLevelSnapshot:
        level_raw = self._controller.get_level()
        return TankLevelSnapshot(level_percent=level_raw * 25, measured_at=datetime.utcnow())


def create_device_controller() -> DeviceControllerAdapter:
    controller = DeviceControllerAdapter()
    controller.setup()
    return controller
