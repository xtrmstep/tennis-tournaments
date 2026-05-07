from __future__ import annotations

import os

from flask import Flask

from .config import Config
from .extensions import db


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)

    from .auth import auth_bp
    from .api.people import people_bp
    from .api.sorting import sorting_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(people_bp, url_prefix="/api/people")
    app.register_blueprint(sorting_bp, url_prefix="/api/sorting")

    with app.app_context():
        # Ensure uploads directory exists
        uploads_dir = os.path.join(app.instance_path, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        db.create_all()

    return app
