# Database Migrations

Single-database configuration managed by [Flask-Migrate](https://flask-migrate.readthedocs.io/) (Alembic).

## Automatic application on startup

When the application starts, the app factory calls `flask_migrate.upgrade()` automatically. This applies all pending Alembic migrations against the configured PostgreSQL database in revision order before the first request is served, so a fresh or outdated database is always brought up to date without manual intervention.

In `TESTING` mode (in-memory SQLite used by the test suite) migrations are skipped; `db.create_all()` is used instead so tests stay fast and self-contained.

## Adding a new migration

Run the following after changing `backend/models.py`:

```bash
DATABASE_URL=sqlite:///tmp_migrate.db uv run flask --app run:app db migrate -m "<short description>"
```

> A temporary SQLite database is used here so that migration files can be generated locally without requiring a running PostgreSQL server. Alembic inspects the SQLAlchemy models, not the live database, to detect schema differences.

This generates a new revision file in `migrations/versions/`. Review the file, then delete the temporary database:

```bash
rm tmp_migrate.db
```

Commit both the model change and the new migration file together.

## Applying migrations manually

To upgrade to the latest revision on a running database:

```bash
DATABASE_URL=<your-db-url> uv run flask --app run:app db upgrade
```

To downgrade one revision:

```bash
DATABASE_URL=<your-db-url> uv run flask --app run:app db downgrade
```

To show the current revision of a database:

```bash
DATABASE_URL=<your-db-url> uv run flask --app run:app db current
```

## Migration template

`script.py.mako` is the Mako template Alembic uses to render each new migration file when `flask db migrate` is run. It should not be removed or modified unless the standard migration file structure needs to change.

