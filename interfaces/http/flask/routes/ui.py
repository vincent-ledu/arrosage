from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_babel import gettext as _

from interfaces.http.flask.container import ServiceContainer

bp = Blueprint("ui", __name__)


def container() -> ServiceContainer:
    return current_app.config["container"]


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/history")
def history_page():
    return render_template("history.html")


@bp.route("/change-lang/<lang_code>")
def change_language(lang_code: str):
    if lang_code in ["fr", "en"]:
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("ui.index"))


@bp.route("/settings/", methods=["GET", "POST"])
def settings_page():
    configuration_service = container().configuration_service
    config = configuration_service.load()

    if request.method == "POST":
        config["pump"] = int(request.form.get("pump", config.get("pump", 2)))
        config["valve"] = int(request.form.get("valve", config.get("valve", 3)))
        config["levels"] = [int(request.form.get(f"level{i}", default)) for i, default in enumerate(config.get("levels", [7, 8, 9, 10]))]

        watering_config = config.setdefault("watering", {})
        for watering_type, settings in watering_config.items():
            settings["threshold"] = int(request.form.get(f"{watering_type}_threshold", settings.get("threshold", 20)))
            settings["morning-duration"] = int(request.form.get(f"{watering_type}_morning-duration", settings.get("morning-duration", 60)))
            settings["evening-duration"] = int(request.form.get(f"{watering_type}_evening-duration", settings.get("evening-duration", 60)))

        config["coordinates"] = {
            "latitude": float(request.form.get("latitude", config.get("coordinates", {}).get("latitude", 48.866667))),
            "longitude": float(request.form.get("longitude", config.get("coordinates", {}).get("longitude", 2.333333))),
        }

        enabled_months = request.form.getlist("enabled_months")
        if enabled_months:
            config["enabled_months"] = [int(m) for m in enabled_months]

        configuration_service.save(config)
        container().device_controller.setup()
        flash(_("Settings saved successfully."), "success")
        return redirect(url_for("ui.settings_page"))

    return render_template("settings.html", config=config)
