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

## GitHub bronze ingestion

```bash
export GITHUB_TOKEN=...
uv run python tools/ingest_github_bronze.py --tenant sandbox
```

For a bounded validation run that does not write to the default local data root:

```bash
uv run python tools/ingest_github_bronze.py \
  --tenant sandbox \
  --data-root /tmp/kabuto-kurage-validation \
  --max-repositories 1
```

## Dagster

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

The current scaffold intentionally has no real Dagster assets. The stable module path lets later tickets add assets without changing the developer command.
