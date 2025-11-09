"""Compatibilité pour les imports historiques ``app.*``."""

from __future__ import annotations

import sys
from types import ModuleType

from . import app as _app_module

__all__ = [
    "app",
    "create_app",
    "get_minmax_temperature_precip",
    "get_temperature_max",
    "forecast",
    "CheckWaterLevel",
    "IfWater",
    "OpenWaterDelay",
    "closeWaterSupply",
    "TTL",
    "ctlInst",
]


class _CompatModule(ModuleType):
    def __getattr__(self, name: str):  # pragma: no cover - délégation
        if hasattr(_app_module, name):
            return getattr(_app_module, name)
        raise AttributeError(f"module 'app' has no attribute '{name}'")

    def __setattr__(self, name: str, value):  # pragma: no cover - délégation
        setattr(_app_module, name, value)
        super().__setattr__(name, getattr(_app_module, name))

    def __dir__(self):  # pragma: no cover - délégation
        return sorted(set(__all__ + dir(_app_module)))


_module = sys.modules[__name__]
_module.__class__ = _CompatModule
for _attr in __all__:
    setattr(_module, _attr, getattr(_app_module, _attr))

del _attr, _module
