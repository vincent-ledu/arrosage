from __future__ import annotations

from typing import Any, Dict

from domain.configuration.repositories import ConfigurationRepository
from config import config as config_module


class FileConfigurationRepository(ConfigurationRepository):
    def load(self) -> Dict[str, Any]:
        return config_module.load_config()

    def save(self, config: Dict[str, Any]) -> None:
        config_module.save_config(config)
