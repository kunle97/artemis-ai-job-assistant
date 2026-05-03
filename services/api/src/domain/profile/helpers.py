"""
Profile domain helper functions.

Contains reusable profile completeness checks.
"""


def detect_missing_fields(profile) -> list[str]:
    """Return profile fields that remain blank after upsert."""
    missing: list[str] = []

    if not profile.phone:
        missing.append("phone")
    if not profile.linkedin_url:
        missing.append("linkedin_url")
    if not profile.github_url:
        missing.append("github_url")
    if not profile.skills:
        missing.append("skills")
    if not profile.city and not profile.state:
        missing.append("location")
    if not profile.work_authorization:
        missing.append("work_authorization")

    return missing
