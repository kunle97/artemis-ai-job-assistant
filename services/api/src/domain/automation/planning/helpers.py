"""
Helper for resolving the correct field classifier based on application URL.
"""

from src.domain.automation.planning.classifiers.ashby import AshbyAutomationFieldClassifier
from src.domain.automation.planning.classifiers.greenhouse import GreenhouseAutomationFieldClassifier
from src.domain.automation.planning.classifiers.generic import GenericAutomationFieldClassifier


def get_classifier_for_url(application_url: str):
    lowered = (application_url or "").lower()

    if "greenhouse" in lowered:
        return GreenhouseAutomationFieldClassifier()

    if "ashbyhq" in lowered or "ashby" in lowered:
        return AshbyAutomationFieldClassifier()

    return GenericAutomationFieldClassifier()