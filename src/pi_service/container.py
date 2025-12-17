from __future__ import annotations

from dataclasses import dataclass

from application.configuration.service import ConfigurationService
from domain.watering.ports import DeviceController
from infrastructure.configuration.file_repository import FileConfigurationRepository
from infrastructure.devices.controllers import create_device_controller
from pi_service.runtime import PiWateringRuntime


@dataclass(slots=True)
class PiServiceContainer:
    configuration_service: ConfigurationService
    device_controller: DeviceController
    watering_runtime: PiWateringRuntime


def build_pi_container() -> PiServiceContainer:
    configuration_repository = FileConfigurationRepository()
    configuration_service = ConfigurationService(configuration_repository)
    controller = create_device_controller()

    runtime = PiWateringRuntime(controller)
    try:
        controller.close_water()
    except Exception:
        pass

    return PiServiceContainer(
        configuration_service=configuration_service,
        device_controller=controller,
        watering_runtime=runtime,
    )
