from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings

# Argumentos de conexión especiales para PostgreSQL (Neon Pooler / Render SSL)
connect_args: dict[str, Any] = {}
raw_pg_url = settings.raw_postgres_url

if settings.is_postgres:
    if "neon.tech" in raw_pg_url and "pooler" in raw_pg_url:
        connect_args["statement_cache_size"] = 0

    query_params = parse_qs(urlsplit(raw_pg_url).query)
    sslmode = query_params.get("sslmode", [""])[0].lower()
    if "render.com" in raw_pg_url or "neon.tech" in raw_pg_url or sslmode in {
        "require",
        "verify-ca",
        "verify-full",
    }:
        connect_args["ssl"] = "require"

# Motor asíncrono compatible con SQLite y PostgreSQL (Render / Neon)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    pool_pre_ping=True,
    connect_args=connect_args,
    future=True,
)

if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Fábrica de sesiones asíncronas
async_session_maker = async_sessionmaker(
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

    added_cupos_disponibles = False

    for table in migrations:
        migration_table = "tour" if table == "tour_disponibles" else table
        column_name, column_type = migrations[table]
        existing_columns = {
            row[1]
            for row in conn.execute(
                text(f'PRAGMA table_info("{migration_table}")')
            ).fetchall()
        }
        if migration_table and column_name not in existing_columns:
            conn.execute(
                text(
                    f'ALTER TABLE "{migration_table}" '
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )
            if table == "tour_disponibles":
                added_cupos_disponibles = True

    if added_cupos_disponibles:
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