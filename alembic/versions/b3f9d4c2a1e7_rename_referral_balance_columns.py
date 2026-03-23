"""rename referral balance columns to general balance

Revision ID: b3f9d4c2a1e7
Revises: 9f2f7b7c1f0a
Create Date: 2026-03-23 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b3f9d4c2a1e7"
down_revision: Union[str, Sequence[str], None] = "9f2f7b7c1f0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("referral_balance", new_column_name="balance")
        batch_op.alter_column("referral_total_earned", new_column_name="total_earned")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("balance", new_column_name="referral_balance")
        batch_op.alter_column("total_earned", new_column_name="referral_total_earned")
