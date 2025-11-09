import sys
from importlib import import_module

_app_cron = import_module("app.cron")

sys.modules[__name__] = _app_cron
