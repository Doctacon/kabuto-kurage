"""CLI wrapper for local GitHub observability.

Examples:

    uv run python tools/observe_github.py --tenant sandbox --format table
    uv run python tools/observe_github.py --all-tenants
"""

from kabuto_kurage.observability import main

if __name__ == "__main__":
    main()
