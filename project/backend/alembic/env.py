import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from logging.config import fileConfig
import os

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

from app.models import Base
target_metadata = Base.metadata

def get_url():
    return os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hardware_tracker")

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=None,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
