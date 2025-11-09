from __future__ import annotations

import atexit
import logging
import os
import sys
from datetime import timedelta
from typing import Dict

from flask import Flask, jsonify, request, session
from flask_babel import Babel, lazy_gettext as _l
from werkzeug.exceptions import HTTPException

import app.config.config as local_config
from babel.messages import mofile, pofile
from interfaces.http.flask.container import build_container
from interfaces.http.flask.routes import system, ui, watering, weather
from routes.history_series import bp as history_series_bp

logger = logging.getLogger(__name__)
ctlInst = None

TTL = timedelta(minutes=30)


def create_app() -> Flask:
    configure_logging()
    _ensure_translations()

    app = Flask(__name__)
    app.secret_key = os.environ.get(
        "SESSION_SECRET_KEY",
        "ish2woo}ng5Ia7sooS0Seukei Vave9oneis1so1zu9Leb1ve&o ailophai0guo-th8jizeiPho4",
    )
    app.config["VERSION"] = local_config.VERSION

    container = build_container(
        ttl=TTL,
        ttl_provider=lambda: getattr(sys.modules.get("app"), "TTL", TTL),
    )
    app.config["container"] = container
    globals()["ctlInst"] = container.device_controller

    babel = Babel(app, locale_selector=get_locale)

    register_context_processors(app)
    register_before_request(app)
    register_blueprints(app)

    atexit.register(lambda: shutdown(container))

    return app


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    environment = os.environ.get("FLASK_ENV", "production")
    log_level = logging.DEBUG if environment == "development" else logging.INFO

    if not os.path.exists("/var/log/gunicorn"):
        os.makedirs("/var/log/gunicorn", exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/var/log/gunicorn/arrosage.log"),
            logging.StreamHandler(),
        ],
    )


def register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_locale():
        return dict(get_locale=get_locale)

    @app.context_processor
    def inject_translations():
        return dict(
            translations={
                "low": _l("Low"),
                "moderate": _l("Moderate"),
                "standard": _l("Standard"),
                "reinforced": _l("Reinforced"),
                "high": _l("High"),
            }
        )

    @app.context_processor
    def inject_version():
        return dict(version=app.config.get("VERSION"))


def register_before_request(app: Flask) -> None:
    @app.before_request
    def log_request_info():
        logger.info("Request received: %s %s", request.method, request.path)

    @app.before_request
    def apply_language_query_param():
        lang = request.args.get("lang")
        if lang in {"fr", "en"}:
            session["lang"] = lang
        elif "lang" not in session:
            session["lang"] = "fr"


def _ensure_translations() -> None:
    translations_root = os.path.join(os.path.dirname(__file__), "translations")
    if not os.path.isdir(translations_root):
        return
    for locale in os.listdir(translations_root):
        mo_path = os.path.join(translations_root, locale, "LC_MESSAGES", "messages.mo")
        po_path = os.path.join(translations_root, locale, "LC_MESSAGES", "messages.po")
        if not os.path.exists(po_path) or os.path.exists(mo_path):
            continue
        os.makedirs(os.path.dirname(mo_path), exist_ok=True)
        with open(po_path, "r", encoding="utf-8") as po_file:
            catalog = pofile.read_po(po_file)
        with open(mo_path, "wb") as mo_file:
            mofile.write_mo(mo_file, catalog)


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(history_series_bp)
    app.register_blueprint(ui.bp)
    app.register_blueprint(weather.bp)
    app.register_blueprint(watering.bp)
    app.register_blueprint(system.bp)


def get_locale():
    if "lang" in session:
        return session["lang"]
    return request.accept_languages.best_match(["fr", "en"])


def shutdown(container) -> None:
    try:
        container.device_controller.cleanup()
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to cleanup device controller")


app = create_app()


@app.errorhandler(Exception)
def handle_generic_error(error):  # pragma: no cover - fallback
    if isinstance(error, HTTPException):
        return error
    logger.exception("Unhandled exception", exc_info=error)
    return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 3000)), debug=False)


def _container():
    return app.config["container"]


def get_minmax_temperature_precip():
    with app.test_request_context():
        return weather.forecast_minmax_precip()


def get_temperature_max():
    with app.test_request_context():
        return weather.temperature_max()


def forecast():
    with app.test_request_context():
        return weather.forecast()


def CheckWaterLevel():
    return watering.water_level()


def IfWater():
    return _container().device_controller.get_level() * 25 > 0


def OpenWaterDelay():
    with app.test_request_context():
        return watering.open_water()


def closeWaterSupply():
    with app.test_request_context():
        return watering.close_water()
