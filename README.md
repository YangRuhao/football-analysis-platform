# Football Analytics Platform

A data engineering and analytics platform for football player statistics across Europe's top five leagues.

## Phase 1 architecture

`Raw CSV → Pandas ETL → PostgreSQL → Materialized View → FastAPI`

Phase 1 focuses on a reliable data/backend foundation before the dashboard is added.

## Local setup

1. Copy the environment template:

   `cp .env.example .env`

2. Replace `DB_PASSWORD` with a long random local password.

3. Start PostgreSQL:

   `docker compose up -d db`

   PostgreSQL is bound to `127.0.0.1` only and uses the dedicated `football_app` database user.

4. Install Python dependencies:

   `pip install -r backend/requirements.txt`

5. Run the API:

   `uvicorn backend.app.main:app --reload --port 8000`

6. Run tests:

   `pytest -q`

   PostgreSQL-backed integration tests run automatically when the configured database is available. Set `REQUIRE_DB_TESTS=1` to make a missing database fail the test run.

## Security and reliability

- Database credentials are supplied through environment variables; insecure default passwords are rejected.
- PostgreSQL is exposed on localhost only by Docker Compose.
- ETL dimension inserts use conflict-safe upserts to avoid concurrent duplicate creation.
- ETL row failures use savepoints so one malformed row does not abort the complete transaction.
- SQL values are parameterized and dynamic leaderboard identifiers are restricted to an explicit allowlist.
- Database constraints provide a second layer of validation for core numeric fields and percentages.
- The API performs a real database health check at startup and through `/health`.
- CI initializes PostgreSQL from the same schema used locally and runs both API and database integration tests.

## Data

See [DATA_SOURCES.md](DATA_SOURCES.md) for provenance, source limitations, transfer handling, and identity rules.

## Phase 1 API

- `GET /health`
- `GET /players/search?name=...`
- `GET /players/{player_id}`
- `GET /players/{player_id}/seasons/{season_label}`
- `GET /compare?player_ids=1&player_ids=2&season=2023-2024`
- `GET /leaderboard?season=2023-2024&metric=goals`

API documentation is available from FastAPI at `/docs` when the service is running.
