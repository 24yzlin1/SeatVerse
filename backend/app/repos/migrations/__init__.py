"""SQL directory for database migrations; currently only the first version, 000_schema.sql.

Migrations are executed by `app.repos.database.run_migrations()`, which runs every
`.sql` file in this directory in filename order; no Python logic lives here directly,
to avoid overlapping responsibilities with the repos layer.
"""
