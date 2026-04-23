"""
Base classifier.

Defines the interface for platform-aware automation field classifiers.
"""

from abc import ABC, abstractmethod


class BaseAutomationFieldClassifier(ABC):
    """
    Base interface for automation field classifiers.
    """

    @abstractmethod
    def classify(
        self,
        *,
        field_type: str,
        label: str | None,
        name: str | None,
        placeholder: str | None,
    ) -> str:
        raise NotImplementedError