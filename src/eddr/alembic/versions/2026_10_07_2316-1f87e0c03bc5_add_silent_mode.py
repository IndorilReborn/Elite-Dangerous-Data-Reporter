"""add_silent_mode

Revision ID: 1f87e0c03bc5
Revises: 663255c37eac
Create Date: 2026-10-07 23:16:41.667150

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1f87e0c03bc5"
down_revision: str | Sequence[str] | None = "663255c37eac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cmdrstatus",
        sa.Column("silent", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cmdrstatus", "silent")
