"""Create job_sources table and seed from deprecated registry."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.domain.jobs.source_registry import JOB_SOURCE_REGISTRY


# revision identifiers, used by Alembic.
revision: str = "20260505_02"
down_revision: Union[str, None] = "20260505_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _seed_rows() -> list[dict]:
    rows: list[dict] = []
    for source, source_map in JOB_SOURCE_REGISTRY.items():
        for company_key, company_config in source_map.items():
            rows.append(
                {
                    "source": source,
                    "company_key": company_key,
                    "board_token": company_config["board_token"],
                    "display_name": company_config["display_name"],
                    "is_active": True,
                }
            )
    return rows


def upgrade() -> None:
    """Create job_sources table and seed it with known company mappings."""
    op.create_table(
        "job_sources",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("company_key", sa.String(length=120), nullable=False),
        sa.Column("board_token", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "company_key", name="uq_job_sources_source_company"),
    )

    job_sources_table = sa.table(
        "job_sources",
        sa.column("source", sa.String),
        sa.column("company_key", sa.String),
        sa.column("board_token", sa.String),
        sa.column("display_name", sa.String),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(job_sources_table, _seed_rows())


def downgrade() -> None:
    """Drop job_sources table."""
    op.drop_table("job_sources")
