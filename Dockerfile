# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.11.4
FROM python:${PYTHON_VERSION}-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.5.27 /uv /uvx /bin/

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create uv's cache dir
RUN mkdir -p /cache/uv
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/cache/uv

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Switch to the non-privileged user to run the application.

# Install dependencies
RUN --mount=type=cache,target=/cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy the source code into the container.
COPY . /app

# Sync the project.
RUN --mount=type=cache,target=/cache/uv \
    uv sync --frozen

# Fix permissions for appuser after installing dependencies
RUN chown -R appuser:appuser /cache/uv /app

USER appuser

CMD ["uv", "run", "python", "-m", "app"]