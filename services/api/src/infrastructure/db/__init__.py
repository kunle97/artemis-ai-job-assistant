"""Database model registry helpers."""


def register_models() -> None:
    """Import all SQLAlchemy models so they are attached to Base metadata."""
    from src.domain.application_answers.intents.models import ApplicationAnswerIntent
    from src.domain.application_answers.models import ApplicationAnswer
    from src.domain.applications.models import Application
    from src.domain.auth.models import RevokedToken, User
    from src.domain.jobs.models import Job, JobPreferences, JobUserFeed
    from src.domain.profile.models import CandidateProfile
    from src.domain.resume.models import Resume

    _ = (
        User,
        RevokedToken,
        CandidateProfile,
        Resume,
        Job,
        JobPreferences,
        JobUserFeed,
        Application,
        ApplicationAnswer,
        ApplicationAnswerIntent,
    )


__all__ = ["register_models"]