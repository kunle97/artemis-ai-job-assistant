"""
Job adapter registry.

Maps source names to adapter implementations.
"""

from src.integrations.adapters.greenhouse.adapter import GreenhouseAdapter
from src.integrations.adapters.ashby.adapter import AshbyAdapter


def get_adapter(source: str):
    """
    Return the adapter implementation for a supported job source.
    """
    normalized_source = source.strip().lower()

    if normalized_source == "greenhouse":
        return GreenhouseAdapter()

    if normalized_source == "ashby":
        return AshbyAdapter()

    raise ValueError(f"Unsupported job source: {source}")