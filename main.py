from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow importing the `app` package when running `python main.py`
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.app import app  # noqa: E402  (import after path setup)


def main() -> None:
    debug_mode = os.environ.get("TESTING", "0") == "1"
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 3000)),
        debug=debug_mode,
    )


if __name__ == "__main__":
    main()
