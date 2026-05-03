"""
Application pipeline service.

Determines whether an application is cleared to advance past the
'filled' state into the submission stage.
"""

import logging

from src.domain.applications.constants import APPLICATION_STATUS_FILLED


logger = logging.getLogger(__name__)


class ApplicationPipelineService:
    """
    Governs pipeline transitions for job applications.

    An application that has been filled by automation must pass a manual
    review gate before it can be submitted.  The gate opens when either:

    * ``manual_review_required`` is ``False`` — the user has opted into
      automatic submission via their profile preferences; or
    * ``is_authorized_to_submit`` is ``True`` — the user explicitly called
      the ``POST /applications/{id}/authorize`` endpoint.
    """

    def can_advance_past_filled(self, application) -> bool:
        """Return True if the application is cleared for submission."""
        if application.status != APPLICATION_STATUS_FILLED:
            logger.debug(
                f"[PipelineService] Application {application.id} is not in "
                f"'filled' state (current: {application.status}); "
                "advancement check is not applicable."
            )
            return False

        if not application.manual_review_required:
            logger.info(
                f"[PipelineService] Application {application.id} cleared "
                "for submission: manual review not required (auto-submit mode)."
            )
            return True

        if application.is_authorized_to_submit:
            logger.info(
                f"[PipelineService] Application {application.id} cleared "
                "for submission: user explicitly authorized."
            )
            return True

        logger.info(
            f"[PipelineService] Application {application.id} is halted at "
            "'filled': manual review required and not yet authorized."
        )
        return False
