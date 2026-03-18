FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

WORKDIR /app

ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1

# Installation des dépendances système de base
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY pyproject.toml ./

# Installation des dépendances
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project

# Copie du code
COPY main.py .

# Sync final
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# Utilisateur non-root
USER 1000

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

CMD ["python", "main.py"]
