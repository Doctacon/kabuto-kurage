# Development

This document mirrors the command surface in the README for quick reference.

## Environment

```bash
uv sync
cp .env.example .env
```

Do not commit `.env` or generated data under `.local/`.

## Checks

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

## Dagster

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

The current scaffold intentionally has no real Dagster assets. The stable module path lets later tickets add assets without changing the developer command.
