"""Dagster code location for the local portfolio project.

The first scaffold intentionally exposes an empty Definitions object. Downstream tickets
will add GitHub ingestion, Delta Lake, and metric assets here without changing the
Dagster startup command documented in the README.
"""

from dagster import Definitions

defs = Definitions(assets=[])
