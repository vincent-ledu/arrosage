import sys
from importlib import import_module

_app_db = import_module("app.db")
sys.modules[__name__] = _app_db

_app_db_database = import_module("app.db.database")
sys.modules.setdefault("db.database", _app_db_database)

_app_db_models = import_module("app.db.models")
sys.modules.setdefault("db.models", _app_db_models)
