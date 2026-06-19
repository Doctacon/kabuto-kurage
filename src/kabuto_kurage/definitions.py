"""Dagster code location for the local portfolio project.

The GitHub asset graph is the first user-facing surface for the project. Start it with:

    uv run dagster dev -m kabuto_kurage.definitions
"""

from kabuto_kurage.assets.github import github_definitions

defs = github_definitions()
