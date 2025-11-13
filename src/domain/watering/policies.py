from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping

from domain.shared.exceptions import DomainError
from domain.watering.entities import TankLevelSnapshot


@dataclass(slots=True)
class WateringPolicy:
    enabled_months: Iterable[int]
    watering_thresholds: Mapping[str, Mapping[str, int]]
    min_temperature_celsius: float = 5.0

    def ensure_can_start(
        self,
        today: date,
        min_temperature: float,
        tank_level: TankLevelSnapshot,
    ) -> None:
        if today.month not in set(self.enabled_months):
            raise DomainError("Watering is disabled for the current month.")

        if min_temperature < self.min_temperature_celsius:
            raise DomainError("Temperature is too low to water.")

        if not tank_level.has_water():
            raise DomainError("Not enough water.")

    def classify_temperature(self, temperature: float) -> str:
        if temperature is None:
            return "unknown"

        sorted_levels = sorted(
            self.watering_thresholds.items(),
            key=lambda item: item[1].get("threshold", 0),
        )
        for level_name, settings in sorted_levels:
            if temperature < settings.get("threshold", 0):
                return level_name
        return sorted_levels[-1][0] if sorted_levels else "unknown"

    def duration_for_period(self, watering_type: str, period: str) -> int:
        period_key = f"{period}-duration"
        config = self.watering_thresholds.get(watering_type)
        if not config:
            raise DomainError(f"Unknown watering type '{watering_type}'.")
        if period_key not in config:
            raise DomainError(f"Missing '{period_key}' duration for '{watering_type}'.")
        return int(config[period_key])
