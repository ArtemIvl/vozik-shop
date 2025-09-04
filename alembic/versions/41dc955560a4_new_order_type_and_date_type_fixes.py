"""New order type and date type fixes

Revision ID: 41dc955560a4
Revises: c8396aae5b97
Create Date: 2025-07-19 17:45:30.091104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '41dc955560a4'
down_revision: Union[str, Sequence[str], None] = 'c8396aae5b97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # создаём ENUM тип вручную
    order_type_enum = postgresql.ENUM('STARS', 'PREMIUM', name='ordertype')
    order_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('orders', sa.Column('premium_months', sa.Integer(), nullable=True))
    op.add_column('orders', sa.Column('order_type', order_type_enum, nullable=True))
    op.alter_column('orders', 'payment_type',
               existing_type=postgresql.ENUM('TON', 'USDT', name='paymenttype'),
               nullable=False)
    op.alter_column('orders', 'memo',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('orders', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False)
    op.drop_column('orders', 'price_usd')
    op.alter_column('users', 'reg_date',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False)
    op.add_column('withdrawals', sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.drop_column('withdrawals', 'reg_date')
    # ### end Alembic commands ###


def downgrade() -> None:
    op.add_column('withdrawals', sa.Column('reg_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_column('withdrawals', 'created_at')
    op.alter_column('users', 'reg_date',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)
    op.add_column('orders', sa.Column('price_usd', sa.NUMERIC(precision=18, scale=8), autoincrement=False, nullable=True))
    op.alter_column('orders', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('orders', 'memo',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('orders', 'payment_type',
               existing_type=postgresql.ENUM('TON', 'USDT', name='paymenttype'),
               nullable=True)

    op.drop_column('orders', 'order_type')
    op.drop_column('orders', 'premium_months')

    # удаляем ENUM тип вручную
    order_type_enum = postgresql.ENUM('STARS', 'PREMIUM', name='ordertype')
    order_type_enum.drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###
