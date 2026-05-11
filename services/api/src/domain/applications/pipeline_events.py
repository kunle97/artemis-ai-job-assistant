"""
Pipeline event log schema.

Defines the ``PipelineEvent`` dataclass used as a structured log record
emitted at each automation pipeline stage transition. These are NOT
persisted to the database — they are emitted as JSON-structured log lines
to support log aggregation and observability.
"""

import json
import logging
from dataclasses import asdict, dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PipelineEvent:
    """Structured log schema for a single pipeline stage event.

    Fields
    ------
    application_id:
        The ID of the application being processed.
    stage:
        The pipeline stage name. One of:
        ``snapshot_capture``, ``inspect``, ``plan``, ``fill``, ``submit``,
        ``pipeline``.
    outcome:
        The result of the stage. One of: ``started``, ``completed``, ``failed``.
    field_count:
        Number of form fields involved in the stage, when applicable.
    error_type:
        Classified error category from ``_classify_failure``, when the
        outcome is ``failed``.
    duration_ms:
        Wall-clock time in milliseconds for the stage, when applicable.
    """

    application_id: int | str
    stage: str
    outcome: str
    field_count: Optional[int] = None
    error_type: Optional[str] = None
    duration_ms: Optional[float] = None


def emit_pipeline_event(event: PipelineEvent) -> None:
    """Emit a ``PipelineEvent`` as a single JSON-structured log line."""
    logger.info("[PipelineEvent] %s", json.dumps(asdict(event), default=str))
