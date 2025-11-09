from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StartManualWateringCommand:
    duration_seconds: int


@dataclass(slots=True)
class StopWateringCommand:
    pass
