import sys
from importlib import import_module

_cron_module = import_module("scripts.cron")

sys.modules[__name__] = _cron_module
