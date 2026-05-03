"""Add min_salary and convert work_arrangement to JSONB array on candidate_profiles."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260503_02"
down_revision: Union[str, None] = "20260503_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add min_salary and migrate work_arrangement string -> JSONB array."""
    op.add_column(
        "candidate_profiles",
        sa.Column("min_salary", sa.String(), nullable=True),
    )

    op.add_column(
        "candidate_profiles",
        sa.Column("work_arrangement_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Preserve any existing single-value work_arrangement as a one-item array.
    op.execute(
        """
        UPDATE candidate_profiles
        SET work_arrangement_jsonb =
            CASE
                WHEN work_arrangement IS NULL OR btrim(work_arrangement) = '' THEN NULL
                ELSE to_jsonb(ARRAY[work_arrangement])
            END
        """
    )

    op.drop_column("candidate_profiles", "work_arrangement")
    op.alter_column(
        "candidate_profiles",
        "work_arrangement_jsonb",
        new_column_name="work_arrangement",
    )


def downgrade() -> None:
    """Revert work_arrangement JSONB array -> string and drop min_salary."""
    op.add_column(
        "candidate_profiles",
        sa.Column("work_arrangement_text", sa.String(), nullable=True),
    )

    # Restore the first array element for legacy string column.
    op.execute(
        """
        UPDATE candidate_profiles
        SET work_arrangement_text =
            CASE
                WHEN work_arrangement IS NULL THEN NULL
                WHEN jsonb_typeof(work_arrangement) = 'array' THEN work_arrangement->>0
                ELSE NULL
            END
        """
    )

    op.drop_column("candidate_profiles", "work_arrangement")
    op.alter_column(
        "candidate_profiles",
        "work_arrangement_text",
        new_column_name="work_arrangement",
    )

    op.drop_column("candidate_profiles", "min_salary")
