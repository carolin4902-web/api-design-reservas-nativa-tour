# app/core/database.py
from collections.abc import AsyncIterator
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

DATABASE_URL = "sqlite+aiosqlite:///./database.db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncIterator[AsyncSession]:
    """Provee una sesión de base de datos asíncrona por cada petición."""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db() -> None:
    """Inicializa la creación de las tablas en la base de datos."""
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Opcional para reiniciar tablas
        await conn.run_sync(SQLModel.metadata.create_all)