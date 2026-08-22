# Database

Postgres + [pgvector](https://github.com/pgvector/pgvector). Schema is defined
in SQL and mirrored by SQLAlchemy models in `backend/app/db/models.py`.

## Migrations

Plain, numbered SQL files in `init/` are the source of truth:

- `init/001_init.sql` — extensions, enum, tables, indexes.

When running via Docker Compose (added in a later step), everything in `init/`
is mounted into `/docker-entrypoint-initdb.d/` and executed automatically the
first time the database container starts.

## Apply manually (against an existing Postgres)

```bash
psql "$DATABASE_URL" -f infra/db/init/001_init.sql
```

`pgvector` must be available to the server for `CREATE EXTENSION vector` to
succeed. The `pgvector/pgvector` Docker image (used in Compose) already includes
it; for a local Postgres install it, then re-run the migration.

## Adding a new migration

Create `init/002_*.sql` with additive changes and keep the ORM models in sync.
