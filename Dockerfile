# syntax=docker/dockerfile:1.7
#
# Base image tracks the *tested* interpreter, not the newest one.
# pyproject declares `requires-python = ">=3.11"` with classifiers to 3.13,
# and the CI matrix runs 3.11 and 3.12 — so shipping a container on 3.14 meant
# production ran a version nothing in this repository had ever executed. A
# Dependabot bump to 3.14 went unnoticed because the CI triggers were wrong and
# no run had fired since. Keep this in step with the test matrix.
# ── builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build deps for any wheels that need to compile from source.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies into a self-contained wheelhouse for the runtime stage.
COPY pyproject.toml requirements.txt ./
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ── web builder ──────────────────────────────────────────────────────
# The React client is a static bundle: it is compiled here and copied into the
# runtime image as plain files, so Node exists at build time only and never
# ships in the final layer.
FROM node:22-slim AS webbuilder

WORKDIR /web

# Dependencies first, so a change to source does not re-resolve the tree.
COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./
RUN npm run build

# ── runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Run as a non-root user.
RUN groupadd --system --gid 1001 kosma \
 && useradd  --system --uid 1001 --gid kosma --home /home/kosma --create-home kosma

# Install only what we need at runtime: curl is used by the HEALTHCHECK.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=kosma:kosma kosma /app/kosma
COPY --chown=kosma:kosma pyproject.toml LICENSE README.md /app/
# Just the compiled output -- no node_modules, no source, no toolchain.
COPY --from=webbuilder --chown=kosma:kosma /web/out /app/web/out

USER kosma

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

# proxy-headers + forwarded-allow-ips lets a reverse proxy pass real client IPs
# to the rate limiter; --no-access-log keeps form requests out of the log.
#
# Shell form so ${PORT} expands: platforms that assign a port at runtime
# (Render among them) inject it as an environment variable, and a container
# that hard-codes 8000 is unreachable there. Falls back to 8000 so `docker run`
# with no environment still works, which is what CI does.
CMD uvicorn kosma.main:app \
      --host 0.0.0.0 \
      --port "${PORT:-8000}" \
      --proxy-headers \
      --forwarded-allow-ips='*' \
      --no-access-log
