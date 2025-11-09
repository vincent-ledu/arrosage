"""Compatibility stub to allow running `python app/app.py`."""

from webapp.app import *  # noqa: F401,F403
from webapp.app import main as _main


if __name__ == "__main__":
    _main()
