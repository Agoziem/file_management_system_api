# Use the official astral/uv image as the base
FROM ghcr.io/astral-sh/uv:python3.11-alpine

# Install postgresql-client for pg_isready (this is necessary even with this base image)
RUN apk add --no-cache postgresql-client

WORKDIR /app

# Copy dependency files first to leverage Docker's build cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


# Copy Alembic configuration file and scripts directory
COPY alembic.ini ./
COPY alembic ./alembic

# Copy the rest of the application code and entrypoint script
COPY app ./app
COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
