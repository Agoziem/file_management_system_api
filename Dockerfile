# Use the official astral/uv image as the base
FROM ghcr.io/astral-sh/uv:python3.11-alpine

# Set the working directory
WORKDIR /app

# Copy dependency files first to leverage Docker's build cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


# Copy the rest of the application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x ./entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]