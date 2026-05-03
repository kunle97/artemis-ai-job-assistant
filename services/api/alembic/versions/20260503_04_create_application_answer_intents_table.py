"""Create application_answer_intents table."""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260503_04"
down_revision: Union[str, None] = "20260503_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create application_answer_intents and supporting indexes."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS application_answer_intents (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            intent_key VARCHAR(100) NOT NULL,
            answer_text TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_application_answer_intent_user_intent UNIQUE (user_id, intent_key)
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_application_answer_intents_user_id
        ON application_answer_intents (user_id)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_application_answer_intents_intent_key
        ON application_answer_intents (intent_key)
        """
    )


def downgrade() -> None:
    """Drop application_answer_intents table."""
    op.execute("DROP TABLE IF EXISTS application_answer_intents")
