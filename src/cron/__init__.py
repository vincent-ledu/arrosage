import sys
from importlib import import_module
from pathlib import Path

# Tests are executed with PYTHONPATH=src, so the repository root (where `scripts` lives)
# is not automatically importable. Add it to sys.path before delegating to scripts.cron.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_cron_module = import_module("scripts.cron")
sys.modules[__name__] = _cron_module
