"""
Manual fill helper functions.

Contains matching logic for user-provided manual field overrides.
"""


def find_matching_override(*, field: dict, overrides: list):
    """Find an override by name first, then by label."""
    field_label = (field.get("label") or "").strip().lower()
    field_name = (field.get("name") or "").strip().lower()

    for override in overrides:
        override_label = (override.label or "").strip().lower()
        override_name = (override.name or "").strip().lower()

        if override_name and field_name and override_name == field_name:
            return override

        if override_label and field_label and override_label == field_label:
            return override

    return None
