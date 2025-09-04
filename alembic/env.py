import os
import sys
import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config, AsyncEngine
from alembic import context
# from src.buy_stars.config import DATABASE_URL
from src.buy_stars.db.base import Base
from src.buy_stars.db import models
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine


# Add parent to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DATABASE_URL = "postgresql+asyncpg://bstars_user:tgstars123@127.0.0.1:5432/bstars_db"

# Alembic config
config = context.config
sync_url = "postgresql+psycopg2://bstars_user:tgstars123@127.0.0.1:5432/bstars_db"
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=None,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()