"""Add resume_id foreign key to applications."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260503_03"
down_revision: Union[str, None] = "20260503_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional resume_id on applications."""
    op.add_column(
        "applications",
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_applications_resume_id_resumes",
        "applications",
        "resumes",
        ["resume_id"],
        ["id"],
    )


def downgrade() -> None:
    """Drop optional resume_id from applications."""
    op.drop_constraint("fk_applications_resume_id_resumes", "applications", type_="foreignkey")
    op.drop_column("applications", "resume_id")
