"""Database model registry helpers."""


def register_models() -> None:
    """Import all SQLAlchemy models so they are attached to Base metadata."""
    from src.domain.application_answers.intents.models import ApplicationAnswerIntent
    from src.domain.application_answers.models import ApplicationAnswer
    from src.domain.applications.followup.models import FollowUp
    from src.domain.applications.models import Application
    from src.domain.auth.models import RevokedToken, User
    from src.domain.jobs.models import Job, JobPreferences, JobSource, JobSourceDiscoveryCandidate, JobUserFeed
    from src.domain.jobs.scoring.models import ApplicationScore
    from src.domain.profile.models import CandidateProfile
    from src.domain.resume.models import Resume

    _ = (
        User,
        RevokedToken,
        CandidateProfile,
        Resume,
        Job,
        JobPreferences,
        JobSource,
        JobSourceDiscoveryCandidate,
        JobUserFeed,
        Application,
        ApplicationAnswer,
        ApplicationAnswerIntent,
        ApplicationScore,
        FollowUp,
    )


__all__ = ["register_models"]