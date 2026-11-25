from app.core.exceptions import ConflictError, NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.Guia import GuiaCreate, GuiaPublic, GuiaUpdate
from app.repositories.guia import GuiaRepository


class GuiaService:
    def __init__(self, guia_repo: GuiaRepository, unit_of_work: UnitOfWork) -> None:
        self.guia_repo = guia_repo
        self.unit_of_work = unit_of_work

    async def get_by_id(self, guia_id: int) -> GuiaPublic:
        guia = await self.guia_repo.get_by_id(guia_id)
        if guia is None:
            raise NotFoundError("Guía no encontrado.")
        return guia

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[GuiaPublic]:
        return await self.guia_repo.get_multi(skip=skip, limit=limit)

    async def create(self, guia_in: GuiaCreate) -> GuiaPublic:
        async with self.unit_of_work.transaction():
            existing = await self.guia_repo.get_by_email(guia_in.correo)
            if existing is not None:
                raise ConflictError("El correo del guía ya existe.")
            return await self.guia_repo.create(guia_in)

    async def update(self, guia_id: int, guia_in: GuiaUpdate) -> GuiaPublic:
        async with self.unit_of_work.transaction():
            if guia_in.correo is not None:
                existing = await self.guia_repo.get_by_email(guia_in.correo)
                if existing is not None and existing.id_guia != guia_id:
                    raise ConflictError("El correo del guía ya existe.")
            guia = await self.guia_repo.update(guia_id, guia_in)
            if guia is None:
                raise NotFoundError("Guía no encontrado.")
            return guia

    async def delete(self, guia_id: int) -> None:
        async with self.unit_of_work.transaction():
            if await self.guia_repo.has_tours(guia_id):
                raise ConflictError(
                    "No se puede eliminar el guía porque tiene tours asociados."
                )
            deleted = await self.guia_repo.delete(guia_id)
            if not deleted:
                raise NotFoundError("Guía no encontrado.")
