from __future__ import annotations

import secrets
from pathlib import Path

from urllib.parse import urlparse

from flask import Flask, abort, current_app, request, session, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object("tour_femmes.config.Config")

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    if app.config.get("AUTO_CREATE_SCHEMA", True):
        _ensure_schema(app)

    from tour_femmes.models import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_helpers() -> dict[str, object]:
        return {
            "csrf_token": _csrf_token,
            "pcs_image_url": _pcs_image_url,
        }

    @app.before_request
    def protect_forms() -> None:
        if request.method != "POST":
            return
        sent_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        if not sent_token or sent_token != session.get("_csrf_token"):
            abort(400, "Invalid CSRF token")

    from tour_femmes.auth import auth_bp
    from tour_femmes.events import events_bp
    from tour_femmes.admin import admin_bp
    from tour_femmes.media import media_bp
    from tour_femmes.cli import register_cli

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(media_bp)
    register_cli(app)

    return app


def _csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def _pcs_image_url(source_url: str | None) -> str:
    if not source_url:
        return ""
    parsed = urlparse(source_url)
    pcs_host = urlparse(current_app.config["PCS_BASE_URL"]).netloc.lower()
    if parsed.scheme in {"http", "https"} and parsed.netloc.lower() == pcs_host:
        return url_for("media.pcs_image", url=source_url)
    return source_url


def _ensure_schema(app: Flask) -> None:
    with app.app_context():
        from tour_femmes import models as _models  # noqa: F401

        db.create_all()
        inspector = inspect(db.engine)
        if inspector.has_table("team"):
            team_columns = {column["name"] for column in inspector.get_columns("team")}
            if "image_url" not in team_columns:
                db.session.execute(text("ALTER TABLE team ADD COLUMN image_url VARCHAR(500)"))
                db.session.commit()
        if inspector.has_table("user_stage_rider_score"):
            score_columns = {
                column["name"]
                for column in inspector.get_columns("user_stage_rider_score")
            }
            for column_name in (
                "classification_points",
                "teammate_points",
                "final_classification_points",
                "final_teammate_points",
            ):
                if column_name not in score_columns:
                    db.session.execute(
                        text(
                            f"ALTER TABLE user_stage_rider_score "
                            f"ADD COLUMN {column_name} INTEGER NOT NULL DEFAULT 0"
                        )
                    )
            db.session.commit()

        # PythonAnywhere forks its web workers after importing the WSGI app.
        # Do not leave a connection opened during application startup.
        db.session.remove()
        # Disposing an in-memory SQLite engine deletes the test database.
        if db.engine.dialect.name != "sqlite":
            db.engine.dispose()
