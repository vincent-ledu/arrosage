import sys
from importlib import import_module

_app_config = import_module("app.config")
_app_config_module = import_module("app.config.config")

sys.modules[__name__] = _app_config
sys.modules.setdefault("config.config", _app_config_module)
