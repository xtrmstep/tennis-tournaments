from __future__ import annotations

import os

from flask import Flask

from .config import Config
from .extensions import db, migrate


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)
    migrate.init_app(app, db)

    from .auth import auth_bp
    from .api.people import people_bp
    from .api.sorting import sorting_bp
    from .api.admin import admin_bp
    from .api.users import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(people_bp, url_prefix="/api/people")
    app.register_blueprint(sorting_bp, url_prefix="/api/sorting")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    with app.app_context():
        # Ensure uploads directory exists
        uploads_dir = os.path.join(app.instance_path, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        if app.config.get("TESTING"):
            # In-memory SQLite used by tests: create tables directly so tests
            # don't depend on migration files being present.
            db.create_all()
        else:
            # All other environments (PostgreSQL, local SQLite dev): apply all
            # pending Alembic migrations automatically on startup.
            from flask_migrate import upgrade
            upgrade()

    return app
