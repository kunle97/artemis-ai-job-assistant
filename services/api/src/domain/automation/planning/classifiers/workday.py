"""
Workday field classifier.
"""

from src.domain.automation.planning.classifiers.generic import GenericAutomationFieldClassifier


class WorkdayAutomationFieldClassifier(GenericAutomationFieldClassifier):
    """
    Workday-aware classifier.

    For now this inherits generic behavior, but it gives us a hook for
    Workday-specific field quirks later.
    """
    pass