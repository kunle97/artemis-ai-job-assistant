"""
Unit tests for demographic autofill flag gating in resolve_demographic_value().

Verifies that each autofill_* flag on CandidateProfile is respected:
- When the flag is False, the resolver returns None (field is skipped).
- When the flag is True, the resolver returns the stored value.
"""

import pytest

from src.domain.automation.planning.helpers import resolve_demographic_value


class _Profile:
    """Minimal profile stub for resolver tests."""

    def __init__(self, **kwargs):
        defaults = {
            "gender": "Male",
            "race": "Asian",
            "veteran_status": "I am not a protected veteran",
            "disability_status": "No, I don't have a disability",
            "pronouns": "He/Him",
            "autofill_gender": False,
            "autofill_race": False,
            "autofill_veteran_status": False,
            "autofill_disability_status": False,
            "autofill_pronouns": False,
        }
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# Gender
# ---------------------------------------------------------------------------


def test_gender_skipped_when_flag_is_false():
    profile = _Profile(autofill_gender=False)
    result = resolve_demographic_value(
        inspected_field={"label": "Gender", "name": None},
        profile=profile,
    )
    assert result is None


def test_gender_resolved_when_flag_is_true():
    profile = _Profile(autofill_gender=True, gender="Male")
    result = resolve_demographic_value(
        inspected_field={"label": "Gender", "name": None},
        profile=profile,
    )
    assert result == "Male"


def test_gender_matched_by_eeo_field_name():
    profile = _Profile(autofill_gender=True, gender="Female")
    result = resolve_demographic_value(
        inspected_field={"label": "", "name": "eeo[gender]"},
        profile=profile,
    )
    assert result == "Female"


# ---------------------------------------------------------------------------
# Race / ethnicity
# ---------------------------------------------------------------------------


def test_race_skipped_when_flag_is_false():
    profile = _Profile(autofill_race=False)
    result = resolve_demographic_value(
        inspected_field={"label": "Race", "name": None},
        profile=profile,
    )
    assert result is None


def test_race_resolved_when_flag_is_true():
    profile = _Profile(autofill_race=True, race="Asian")
    result = resolve_demographic_value(
        inspected_field={"label": "Ethnicity", "name": None},
        profile=profile,
    )
    assert result == "Asian"


def test_race_matched_by_eeo_field_name():
    profile = _Profile(autofill_race=True, race="Asian")
    result = resolve_demographic_value(
        inspected_field={"label": "", "name": "eeo[race]"},
        profile=profile,
    )
    assert result == "Asian"


# ---------------------------------------------------------------------------
# Veteran status
# ---------------------------------------------------------------------------


def test_veteran_skipped_when_flag_is_false():
    profile = _Profile(autofill_veteran_status=False)
    result = resolve_demographic_value(
        inspected_field={"label": "Veteran Status", "name": None},
        profile=profile,
    )
    assert result is None


def test_veteran_resolved_when_flag_is_true():
    profile = _Profile(autofill_veteran_status=True, veteran_status="I am not a protected veteran")
    result = resolve_demographic_value(
        inspected_field={"label": "Protected Veteran", "name": None},
        profile=profile,
    )
    assert result == "I am not a protected veteran"


def test_veteran_matched_by_eeo_field_name():
    profile = _Profile(autofill_veteran_status=True, veteran_status="I am not a protected veteran")
    result = resolve_demographic_value(
        inspected_field={"label": "", "name": "eeo[veteran]"},
        profile=profile,
    )
    assert result == "I am not a protected veteran"


# ---------------------------------------------------------------------------
# Disability status
# ---------------------------------------------------------------------------


def test_disability_skipped_when_flag_is_false():
    profile = _Profile(autofill_disability_status=False)
    result = resolve_demographic_value(
        inspected_field={"label": "Disability Status", "name": None},
        profile=profile,
    )
    assert result is None


def test_disability_resolved_when_flag_is_true():
    profile = _Profile(
        autofill_disability_status=True,
        disability_status="No, I don't have a disability",
    )
    result = resolve_demographic_value(
        inspected_field={"label": "Individual with a Disability", "name": None},
        profile=profile,
    )
    assert result == "No, I don't have a disability"


def test_disability_matched_by_eeo_field_name():
    profile = _Profile(
        autofill_disability_status=True,
        disability_status="No, I don't have a disability",
    )
    result = resolve_demographic_value(
        inspected_field={"label": "", "name": "eeo[disability]"},
        profile=profile,
    )
    assert result == "No, I don't have a disability"


# ---------------------------------------------------------------------------
# Pronouns
# ---------------------------------------------------------------------------


def test_pronouns_skipped_when_flag_is_false():
    profile = _Profile(autofill_pronouns=False)
    result = resolve_demographic_value(
        inspected_field={"label": "Preferred Pronouns", "name": None},
        profile=profile,
    )
    assert result is None


def test_pronouns_resolved_when_flag_is_true():
    profile = _Profile(autofill_pronouns=True, pronouns="He/Him")
    result = resolve_demographic_value(
        inspected_field={"label": "Preferred Pronouns", "name": None},
        profile=profile,
    )
    assert result == "He/Him"


def test_pronouns_matched_by_field_name():
    profile = _Profile(autofill_pronouns=True, pronouns="They/Them")
    result = resolve_demographic_value(
        inspected_field={"label": "", "name": "pronouns"},
        profile=profile,
    )
    assert result == "They/Them"


# ---------------------------------------------------------------------------
# All flags False simultaneously (no leakage)
# ---------------------------------------------------------------------------


def test_all_flags_false_no_leakage():
    """Confirms that a fully populated profile leaks nothing when all flags are off."""
    profile = _Profile()  # all autofill_* default to False

    for field in [
        {"label": "Gender", "name": None},
        {"label": "Race", "name": None},
        {"label": "Veteran Status", "name": None},
        {"label": "Disability Status", "name": None},
        {"label": "Preferred Pronouns", "name": None},
    ]:
        assert resolve_demographic_value(inspected_field=field, profile=profile) is None


# ---------------------------------------------------------------------------
# Profile has None value (flag True but no stored value)
# ---------------------------------------------------------------------------


def test_gender_flag_true_but_no_value_stored():
    profile = _Profile(autofill_gender=True, gender=None)
    result = resolve_demographic_value(
        inspected_field={"label": "Gender", "name": None},
        profile=profile,
    )
    assert result is None
