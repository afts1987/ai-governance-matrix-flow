# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# Dependencies first, so code changes do not rebuild them
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY scripts ./scripts
COPY tests ./tests

# Data is mounted, never baked in: the matrix, profile, sources and history belong to the organisation.
VOLUME ["/app/data"]

# Non-root user; the agent reads the web and holds credentials, so it should not run as root.
RUN useradd -m -u 1000 flow && chown -R flow:flow /app
USER flow

ENV HITL_MODE=file
ENTRYPOINT ["matrix-flow"]
