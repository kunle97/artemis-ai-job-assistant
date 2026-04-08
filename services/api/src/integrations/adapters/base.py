"""
Job source adapter base classes.

Defines the interface all job-source adapters must implement.
"""

from abc import ABC, abstractmethod


class JobSourceAdapter(ABC):
    """
    Base interface for all job source adapters.
    """

    @abstractmethod
    def search_jobs(
        self,
        board_token: str | None = None,
        query: str | None = None,
        location: str | None = None,
    ) -> list[dict]:
        """
        Search jobs from a source and return normalized job dictionaries.
        """
        raise NotImplementedError