"""add processing order status

Revision ID: 522acf46fd38
Revises: 695ab68c42de
Create Date: 2025-08-04 15:20:53.987164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '522acf46fd38'
down_revision = '695ab68c42de'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'PROCESSING'")

def downgrade() -> None:
    # Удалить значение из Enum нельзя, обычно делают откат в downgrade через recreate типа
    pass
