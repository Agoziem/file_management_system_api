#!/bin/sh

set -e

# Wait for PostgreSQL to become available and accept connections
echo "Waiting for Postgres..."
export PGPASSWORD="$POSTGRES_PASSWORD" # PGPASSWORD is needed by pg_isready
until pg_isready -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "Postgres is available. Continuing..."

# Run Alembic migrations
echo "Running Alembic migrations..."
uv run alembic upgrade head

# Start the application
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
