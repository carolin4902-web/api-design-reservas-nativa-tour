from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.Tour import TourCreate, TourPublic, TourUpdate
from app.repositories.guia import GuiaRepository
from app.repositories.tour import TourRepository


class TourService:
    def __init__(
        self,
        tour_repo: TourRepository,
        guia_repo: GuiaRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.tour_repo = tour_repo
        self.guia_repo = guia_repo
        self.unit_of_work = unit_of_work

    async def get_by_id(self, tour_id: int) -> TourPublic:
        tour = await self.tour_repo.get_by_id(tour_id)
        if tour is None:
            raise NotFoundError("Tour no encontrado.")
        return tour

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        guia_id: int | None = None,
    ) -> list[TourPublic]:
        return await self.tour_repo.get_multi(skip=skip, limit=limit, guia_id=guia_id)

    async def create(self, tour_in: TourCreate) -> TourPublic:
        async with self.unit_of_work.transaction():
            guia = await self.guia_repo.get_by_id(tour_in.id_guia)
            if guia is None or not guia.verificado:
                raise BusinessRuleError(
                    "El guía asignado no existe o no está verificado."
                )
            return await self.tour_repo.create(tour_in)

    async def update(self, tour_id: int, tour_in: TourUpdate) -> TourPublic:
        async with self.unit_of_work.transaction():
            tour = await self.get_by_id(tour_id)
            update_data = tour_in.model_dump(exclude_unset=True)

            if "id_guia" in update_data:
                if tour_in.id_guia is None:
                    raise BusinessRuleError("El guía del tour no puede quedar vacío.")
                guia = await self.guia_repo.get_by_id(tour_in.id_guia)
                if guia is None or not guia.verificado:
                    raise BusinessRuleError(
                        "El guía asignado no existe o no está verificado."
                    )

            cupos_disponibles = None
            if "capacidad" in update_data:
                nueva_capacidad = tour_in.capacidad
                if nueva_capacidad is None:
                    raise BusinessRuleError("La capacidad no puede quedar vacía.")
                cupos_ocupados = tour.capacidad - tour.cupos_disponibles
                if nueva_capacidad < cupos_ocupados:
                    raise BusinessRuleError(
                        "La capacidad no puede ser menor que los cupos ya reservados."
                    )
                cupos_disponibles = nueva_capacidad - cupos_ocupados

            updated_tour = await self.tour_repo.update(
                tour_id,
                tour_in,
                cupos_disponibles=cupos_disponibles,
            )
            if updated_tour is None:
                raise NotFoundError("Tour no encontrado.")
            return updated_tour

    async def delete(self, tour_id: int) -> None:
        async with self.unit_of_work.transaction():
            deleted = await self.tour_repo.delete(tour_id)
            if not deleted:
                raise NotFoundError("Tour no encontrado.")
