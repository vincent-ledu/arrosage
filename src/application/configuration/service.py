from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from domain.configuration.repositories import ConfigurationRepository


@dataclass(slots=True)
class ConfigurationService:
    repository: ConfigurationRepository

    def load(self) -> Dict[str, Any]:
        return self.repository.load()

    def save(self, config: Dict[str, Any]) -> None:
        self.repository.save(config)
