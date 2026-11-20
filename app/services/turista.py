from app.core.exceptions import ConflictError, NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.Turista import TuristaCreate, TuristaPublic, TuristaUpdate
from app.repositories.turista import TuristaRepository


class TuristaService:
    def __init__(
        self, turista_repo: TuristaRepository, unit_of_work: UnitOfWork
    ) -> None:
        self.turista_repo = turista_repo
        self.unit_of_work = unit_of_work

    async def get_by_id(self, turista_id: int) -> TuristaPublic:
        turista = await self.turista_repo.get_by_id(turista_id)
        if turista is None:
            raise NotFoundError("Turista no encontrado.")
        return turista

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[TuristaPublic]:
        return await self.turista_repo.get_multi(skip=skip, limit=limit)

    async def create(self, turista_in: TuristaCreate) -> TuristaPublic:
        async with self.unit_of_work.transaction():
            existing = await self.turista_repo.get_by_email(turista_in.correo)
            if existing is not None:
                raise ConflictError("El correo ya está registrado.")
            return await self.turista_repo.create(turista_in)

    async def update(self, turista_id: int, turista_in: TuristaUpdate) -> TuristaPublic:
        async with self.unit_of_work.transaction():
            turista = await self.turista_repo.update(turista_id, turista_in)
            if turista is None:
                raise NotFoundError("Turista no encontrado.")
            return turista

    async def delete(self, turista_id: int) -> None:
        async with self.unit_of_work.transaction():
            deleted = await self.turista_repo.delete(turista_id)
            if not deleted:
                raise NotFoundError("Turista no encontrado.")
