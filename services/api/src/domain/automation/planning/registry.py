"""
Classifier registry.

Maps detected platforms to the right field classifier.
"""

from src.domain.automation.planning.classifiers.ashby import AshbyAutomationFieldClassifier
from src.domain.automation.planning.classifiers.generic import GenericAutomationFieldClassifier
from src.domain.automation.planning.classifiers.greenhouse import GreenhouseAutomationFieldClassifier


def get_field_classifier(platform: str):
    if platform == "greenhouse":
        return GreenhouseAutomationFieldClassifier()

    if platform == "ashby":
        return AshbyAutomationFieldClassifier()

    return GenericAutomationFieldClassifier()