"""CLI wrapper for GitHub bronze ingestion.

Run from the repository root, for example:

    uv run python tools/ingest_github_bronze.py --tenant sandbox
"""

from kabuto_kurage.ingestion.github_bronze import main

if __name__ == "__main__":
    main()
