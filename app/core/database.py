from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

# Argumentos de conexión especiales (ej. desactivar statement cache si se usa Neon Pooler)
connect_args: dict[str, Any] = {}

if "neon.tech" in settings.DATABASE_URL and "pooler" in settings.DATABASE_URL:
    connect_args["statement_cache_size"] = 0

# Motor asíncrono compatible con SQLite y Neon PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    pool_pre_ping=True,
    connect_args=connect_args,
    future=True,
)

# Fábrica de sesiones asíncronas
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def init_db() -> None:
    """Crea las tablas en la base de datos si no existen."""
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.run_sync(_migrate_sqlite_columns)


def _migrate_sqlite_columns(conn: Any) -> None:
    """Agrega columnas nuevas sin reemplazar bases SQLite existentes."""
    if engine.dialect.name != "sqlite":
        return

    migrations = {
        "turista": ("activo", "BOOLEAN NOT NULL DEFAULT 1"),
        "guia": ("verificado", "BOOLEAN NOT NULL DEFAULT 0"),
        "tour": ("activo", "BOOLEAN NOT NULL DEFAULT 1"),
        "tour_disponibles": ("cupos_disponibles", "INTEGER NOT NULL DEFAULT 0"),
    }

    for table in migrations:
        migration_table = "tour" if table == "tour_disponibles" else table
        column_name, column_type = migrations[table]
        existing_columns = {
            row[1] for row in conn.execute(
                text(f'PRAGMA table_info("{migration_table}")')
            ).fetchall()
        }
        if migration_table and column_name not in existing_columns:
            conn.execute(
                text(
                    f'ALTER TABLE "{migration_table}" '
                    f'ADD COLUMN {column_name} {column_type}'
                )
            )

    if "tour" in migrations:
        conn.execute(
            text(
                "UPDATE tour SET cupos_disponibles = capacidad "
                "WHERE cupos_disponibles = 0"
            )
        )

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI para obtener la sesión de base de datos."""
    async with async_session_maker() as session:
        yield session