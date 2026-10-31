
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

# 1. Base Común
class TuristaBase(SQLModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=1, max_length=150, index=True)
    telefono: str = Field(min_length=1, max_length=20)


# 2. Tabla de Base de Datos
class Turista(TuristaBase, table=True):
    __tablename__ = "turista"

    id_turista: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# 3. DTO de Entrada (POST)
class TuristaCreate(TuristaBase):
    pass


# 4. DTO de Edición (PATCH)
class TuristaUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    correo: str | None = Field(default=None, min_length=1, max_length=150)
    telefono: str | None = Field(default=None, min_length=1, max_length=20)


# 5. DTO de Salida (GET)
class TuristaPublic(TuristaBase):
    id_turista: int
    created_at: datetime
    updated_at: datetime
