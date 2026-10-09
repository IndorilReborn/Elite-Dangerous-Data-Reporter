"""add_current_ship_data

Revision ID: 663255c37eac
Revises: 5959e3d56550
Create Date: 2026-10-01 10:33:49.908767

"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

import eddr.db
from eddr.journal_schemas.loadout import FuelCapacity, Loadout

# revision identifiers, used by Alembic.
revision: str = "663255c37eac"
down_revision: str | Sequence[str] | None = "5959e3d56550"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DELETE FROM journalfile")  # Need to reread as not optional
    op.add_column(
        "cmdrstatus",
        sa.Column(
            "current_ship_slef",
            eddr.db.PydanticJSON(eddr.db.Loadout),
            nullable=False,
            server_default=Loadout(
                timestamp=datetime.now(UTC),
                Ship="",
                ShipID=0,
                ShipName="",
                ShipIdent="",
                UnladenMass=0,
                CargoCapacity=0,
                MaxJumpRange=0,
                FuelCapacity=FuelCapacity(Main=0.0, Reserve=0.0),
                Rebuy=0,
                Modules=[],
            ).model_dump_json(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cmdrstatus", "current_ship_slef")
