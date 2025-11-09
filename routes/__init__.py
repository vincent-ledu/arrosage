import sys
from importlib import import_module

_app_routes = import_module("app.routes")

sys.modules[__name__] = _app_routes
