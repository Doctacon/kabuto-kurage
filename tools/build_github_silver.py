"""CLI wrapper for GitHub silver transformations.

Run from the repository root after bronze ingestion, for example:

    uv run python tools/build_github_silver.py --tenant sandbox
"""

from kabuto_kurage.transforms.github_silver import main

if __name__ == "__main__":
    main()
