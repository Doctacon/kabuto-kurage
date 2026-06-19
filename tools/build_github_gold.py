"""CLI wrapper for GitHub gold metric materialization.

Run from the repository root after bronze and silver tables exist, for example:

    uv run python tools/build_github_gold.py --tenant sandbox
"""

from kabuto_kurage.transforms.github_gold import main

if __name__ == "__main__":
    main()
