"""add hotel max_bot_token

Revision ID: a1b2c3d4e5f6
Revises: df71ba22e9c4
Create Date: 2026-04-05 23:00:00.000000

"""

from typing import Sequence, Union  # noqa: UP035

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "df71ba22e9c4"  # noqa: UP007
branch_labels: Union[str, Sequence[str], None] = None  # noqa: UP007
depends_on: Union[str, Sequence[str], None] = None  # noqa: UP007


def upgrade() -> None:
    op.add_column(
        "hotels",
        sa.Column("max_bot_token", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        op.f("uq__hotels__max_bot_token"),
        "hotels",
        ["max_bot_token"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq__hotels__max_bot_token"), "hotels", type_="unique")
    op.drop_column("hotels", "max_bot_token")
