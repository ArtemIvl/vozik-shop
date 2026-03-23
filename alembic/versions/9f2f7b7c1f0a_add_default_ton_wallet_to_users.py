"""add default ton wallet to users

Revision ID: 9f2f7b7c1f0a
Revises: e5169502af08
Create Date: 2026-03-23 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f2f7b7c1f0a"
down_revision: Union[str, Sequence[str], None] = "e5169502af08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("default_ton_wallet", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "default_ton_wallet")
