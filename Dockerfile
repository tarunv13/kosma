# syntax=docker/dockerfile:1.7
#
# Base image tracks the *tested* interpreter, not the newest one.
# pyproject declares `requires-python = ">=3.11"` with classifiers to 3.13,
# and the CI matrix runs 3.11 and 3.12 — so shipping a container on 3.14 meant
# production ran a version nothing in this repository had ever executed. A
# Dependabot bump to 3.14 went unnoticed because the CI triggers were wrong and
# no run had fired since. Keep this in step with the test matrix.
# ── builder ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS builder

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

# ── runtime ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS runtime

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

USER kosma

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

# proxy-headers + forwarded-allow-ips lets a reverse proxy pass real client IPs
# to the rate limiter; --no-access-log keeps form requests out of the log.
CMD ["uvicorn", "kosma.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--proxy-headers", \
     "--forwarded-allow-ips=*", \
     "--no-access-log"]
