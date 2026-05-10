"""
Unit tests for demographic field classification across platforms.

Verifies that pronoun, gender, veteran, disability, and work-authorization
fields are correctly classified on Generic, Greenhouse, Lever, and Ashby sites.
"""

import pytest

from src.domain.automation.planning.classifiers.generic import GenericAutomationFieldClassifier
from src.domain.automation.planning.classifiers.greenhouse import GreenhouseAutomationFieldClassifier
from src.domain.automation.planning.classifiers.lever import LeverAutomationFieldClassifier
from src.domain.automation.planning.classifiers.ashby import AshbyAutomationFieldClassifier
from src.domain.automation.planning.constants import (
    FIELD_ROLE_DESIRED_START_DATE,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_OPEN_ENDED,
    FIELD_ROLE_WORK_ARRANGEMENT,
    FIELD_ROLE_WORK_AUTHORIZATION,
)


# ---------------------------------------------------------------------------
# Pronouns — Generic
# ---------------------------------------------------------------------------


def test_generic_classifies_preferred_pronouns_label():
    clf = GenericAutomationFieldClassifier()
    role = clf.classify(
        field_type="select_like",
        label="Preferred Pronouns",
        name=None,
        placeholder=None,
    )
    assert role == FIELD_ROLE_DEMOGRAPHIC


def test_generic_classifies_pronouns_field_name():
    clf = GenericAutomationFieldClassifier()
    role = clf.classify(
        field_type="select_like",
        label=None,
        name="pronouns",
        placeholder=None,
    )
    assert role == FIELD_ROLE_DEMOGRAPHIC


def test_generic_classifies_pronouns_radio_group():
    clf = GenericAutomationFieldClassifier()
    role = clf.classify(
        field_type="radio_group",
        label="What are your preferred pronouns?",
        name=None,
        placeholder=None,
    )
    assert role == FIELD_ROLE_DEMOGRAPHIC


# ---------------------------------------------------------------------------
# Pronouns — Greenhouse
# ---------------------------------------------------------------------------


def test_greenhouse_classifies_preferred_pronouns_label():
    clf = GreenhouseAutomationFieldClassifier()
    role = clf.classify(
        field_type="select_like",
        label="Preferred Pronouns",
        name=None,
        placeholder=None,
    )
    assert role == FIELD_ROLE_DEMOGRAPHIC


def test_greenhouse_classifies_pronouns_select():
    clf = GreenhouseAutomationFieldClassifier()
    role = clf.classify(
        field_type="select",
        label="Pronouns",
        name=None,
        placeholder=None,
    )
    assert role == FIELD_ROLE_DEMOGRAPHIC


# ---------------------------------------------------------------------------
# Pronouns — Lever (already worked, confirm no regression)
# ---------------------------------------------------------------------------


def test_lever_classifies_pronouns_field_name():
    clf = LeverAutomationFieldClassifier()
    role = clf.classify(
        field_type="select_like",
        label="Preferred Pronouns",
        name="pronouns",
        placeholder=None,
    )
    assert role == FIELD_ROLE_DEMOGRAPHIC


# ---------------------------------------------------------------------------
# Pronouns — Ashby (already worked, confirm no regression)
# ---------------------------------------------------------------------------


def test_ashby_classifies_preferred_pronouns():
    clf = AshbyAutomationFieldClassifier()
    role = clf.classify(
        field_type="select_like",
        label="Preferred Pronouns",
        name=None,
        placeholder=None,
    )
    assert role == FIELD_ROLE_DEMOGRAPHIC


# ---------------------------------------------------------------------------
# Gender — all platforms
# ---------------------------------------------------------------------------


def test_generic_classifies_gender():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Gender", name=None, placeholder=None) == FIELD_ROLE_DEMOGRAPHIC


def test_greenhouse_classifies_gender():
    clf = GreenhouseAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Gender", name=None, placeholder=None) == FIELD_ROLE_DEMOGRAPHIC


# ---------------------------------------------------------------------------
# Veteran status — all platforms
# ---------------------------------------------------------------------------


def test_generic_classifies_veteran_status():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Veteran Status", name=None, placeholder=None) == FIELD_ROLE_DEMOGRAPHIC


def test_greenhouse_classifies_veteran_status():
    clf = GreenhouseAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Veteran Status", name=None, placeholder=None) == FIELD_ROLE_DEMOGRAPHIC


def test_lever_classifies_veteran_eeo_field_name():
    clf = LeverAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Veteran Status", name="eeo[veteran]", placeholder=None) == FIELD_ROLE_DEMOGRAPHIC


# ---------------------------------------------------------------------------
# Disability status — all platforms
# ---------------------------------------------------------------------------


def test_generic_classifies_disability():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Disability Status", name=None, placeholder=None) == FIELD_ROLE_DEMOGRAPHIC


def test_greenhouse_classifies_disability():
    clf = GreenhouseAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Disability Status", name=None, placeholder=None) == FIELD_ROLE_DEMOGRAPHIC


# ---------------------------------------------------------------------------
# Work authorization — all platforms
# ---------------------------------------------------------------------------


def test_generic_classifies_work_authorization():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Are you authorized to work in the US?", name=None, placeholder=None) == FIELD_ROLE_WORK_AUTHORIZATION


def test_generic_classifies_work_authorization_with_leagally_typo():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(
        field_type="select_like",
        label="Are you leagally authorized to work in the United States?",
        name=None,
        placeholder=None,
    ) == FIELD_ROLE_WORK_AUTHORIZATION


def test_greenhouse_classifies_work_authorization():
    clf = GreenhouseAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Are you authorized to work in the US?", name=None, placeholder=None) == FIELD_ROLE_WORK_AUTHORIZATION


def test_lever_classifies_sponsorship():
    clf = LeverAutomationFieldClassifier()
    assert clf.classify(field_type="select_like", label="Do you require sponsorship to work in the United States?", name=None, placeholder=None) == FIELD_ROLE_WORK_AUTHORIZATION


def test_ashby_classifies_work_authorization():
    clf = AshbyAutomationFieldClassifier()
    assert clf.classify(field_type="radio_group", label="Are you authorized to work in the US?", name=None, placeholder=None) == FIELD_ROLE_WORK_AUTHORIZATION


def test_generic_classifies_hybrid_commute_requirement_as_work_arrangement():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(
        field_type="select_like",
        label="We have a hybrid culture. Are you able to work out of our NY office Monday, Tuesday and Wednesday?*",
        name=None,
        placeholder=None,
    ) == FIELD_ROLE_WORK_ARRANGEMENT


def test_generic_classifies_why_are_you_interested_textarea_as_open_ended():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(
        field_type="textarea",
        label="Why Cognitiv? Why are you interested in this role with us?",
        name=None,
        placeholder=None,
    ) == FIELD_ROLE_OPEN_ENDED


def test_generic_classifies_desired_start_date_question():
    clf = GenericAutomationFieldClassifier()
    assert clf.classify(
        field_type="input",
        label="When can you start?",
        name=None,
        placeholder=None,
    ) == FIELD_ROLE_DESIRED_START_DATE


def test_ashby_classifies_desired_start_date_question():
    clf = AshbyAutomationFieldClassifier()
    assert clf.classify(
        field_type="input",
        label="Desired start date",
        name=None,
        placeholder=None,
    ) == FIELD_ROLE_DESIRED_START_DATE


def test_lever_classifies_desired_start_date_field_name():
    clf = LeverAutomationFieldClassifier()
    assert clf.classify(
        field_type="input",
        label="Availability",
        name="available_start_date",
        placeholder=None,
    ) == FIELD_ROLE_DESIRED_START_DATE
