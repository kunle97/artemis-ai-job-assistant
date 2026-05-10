"""
Application domain constants.

Defines valid application statuses for the Artemis workflow.
"""

APPLICATION_STATUS_SAVED = "saved"
APPLICATION_STATUS_READY = "ready"
APPLICATION_STATUS_NEEDS_REVIEW = "needs_review"

# Pipeline stage statuses (inspect → plan → fill)
APPLICATION_STATUS_QUEUED = "queued"
APPLICATION_STATUS_INSPECTING = "inspecting"
APPLICATION_STATUS_INSPECTED = "inspected"
APPLICATION_STATUS_PLANNING = "planning"
APPLICATION_STATUS_PLANNED = "planned"
APPLICATION_STATUS_FILLING = "filling"
APPLICATION_STATUS_FILLED = "filled"
APPLICATION_STATUS_AWAITING_SUBMISSION = "awaiting_submission"

APPLICATION_STATUS_SUBMITTED = "submitted"
APPLICATION_STATUS_FAILED = "failed"

# Post-application lifecycle statuses (used when importing from Career-Ops tracker
# and when users manually update their status after submission)
APPLICATION_STATUS_APPLIED = "applied"
APPLICATION_STATUS_INTERVIEWING = "interviewing"
APPLICATION_STATUS_OFFER_RECEIVED = "offer_received"
APPLICATION_STATUS_OFFER_ACCEPTED = "offer_accepted"
APPLICATION_STATUS_REJECTED = "rejected"
APPLICATION_STATUS_ARCHIVED = "archived"

# Statuses users are allowed to set manually after a successful submission.
# These represent real-world outcomes the user tracks themselves.
POST_SUBMISSION_LIFECYCLE_STATUSES: frozenset[str] = frozenset({
    APPLICATION_STATUS_INTERVIEWING,
    APPLICATION_STATUS_OFFER_RECEIVED,
    APPLICATION_STATUS_OFFER_ACCEPTED,
    APPLICATION_STATUS_REJECTED,
    APPLICATION_STATUS_ARCHIVED,
})

# All valid statuses that can be manually set by users after submission.
# Includes 'submitted' so users can correct if they selected the wrong status.
ALL_VALID_LIFECYCLE_STATUSES: frozenset[str] = frozenset({
    APPLICATION_STATUS_SUBMITTED,
}) | POST_SUBMISSION_LIFECYCLE_STATUSES

# Applications in SUBMITTED status older than this many days are auto-archived.
AUTO_ARCHIVE_STALE_SUBMISSION_DAYS = 60

APPLICATION_STATUSES = {
    APPLICATION_STATUS_SAVED,
    APPLICATION_STATUS_READY,
    APPLICATION_STATUS_NEEDS_REVIEW,
    APPLICATION_STATUS_QUEUED,
    APPLICATION_STATUS_INSPECTING,
    APPLICATION_STATUS_INSPECTED,
    APPLICATION_STATUS_PLANNING,
    APPLICATION_STATUS_PLANNED,
    APPLICATION_STATUS_FILLING,
    APPLICATION_STATUS_FILLED,
    APPLICATION_STATUS_AWAITING_SUBMISSION,
    APPLICATION_STATUS_SUBMITTED,
    APPLICATION_STATUS_FAILED,
    APPLICATION_STATUS_APPLIED,
    APPLICATION_STATUS_INTERVIEWING,
    APPLICATION_STATUS_OFFER_RECEIVED,
    APPLICATION_STATUS_OFFER_ACCEPTED,
    APPLICATION_STATUS_REJECTED,
    APPLICATION_STATUS_ARCHIVED,
}


# ---------------------------------------------------------------------------
# External status resolver
# ---------------------------------------------------------------------------

_EXTERNAL_STATUS_MAP: dict[str, str] = {
    # Generic import labels → Artemis statuses
    "evaluated": APPLICATION_STATUS_SAVED,
    "applied": APPLICATION_STATUS_APPLIED,
    "responded": APPLICATION_STATUS_APPLIED,
    "interview": APPLICATION_STATUS_INTERVIEWING,
    "offer": APPLICATION_STATUS_OFFER_RECEIVED,
    "rejected": APPLICATION_STATUS_REJECTED,
    "discarded": APPLICATION_STATUS_ARCHIVED,
    "skip": APPLICATION_STATUS_ARCHIVED,
    "submitted": APPLICATION_STATUS_SUBMITTED,
}


def resolve_external_status(raw_status: str) -> str:
    """
    Normalise a raw status string from an external source into an Artemis
    application status.  Comparison is case-insensitive.

    Returns ``saved`` for any unrecognised value so imported records are
    never silently dropped.
    """
    return _EXTERNAL_STATUS_MAP.get(raw_status.lower().strip(), APPLICATION_STATUS_SAVED)