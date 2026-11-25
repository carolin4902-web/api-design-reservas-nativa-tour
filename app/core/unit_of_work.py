from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._depth = 0

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        if self._depth > 0:
            self._depth += 1
            try:
                async with self._session.begin_nested():
                    yield
            finally:
                self._depth -= 1
            return

        self._depth += 1
        try:
            if not self._session.in_transaction():
                async with self._session.begin():
                    yield
            else:
                # Si una lectura previa disparó autobegin, cerramos esa transacción aquí.
                try:
                    yield
                    await self._session.commit()
                except Exception:
                    await self._session.rollback()
                    raise
        finally:
            self._depth -= 1
