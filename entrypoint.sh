#!/bin/sh

set -e

# Run Alembic migrations
echo "Running Alembic migrations..."
uv run alembic upgrade head

# Start the application
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
