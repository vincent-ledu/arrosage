from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ConfigurationRepository(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def save(self, config: Dict[str, Any]) -> None:
        ...
