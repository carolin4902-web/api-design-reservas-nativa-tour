
from typing import Optional

from sqlmodel import Field, SQLModel


class GuiaBase(SQLModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=1, max_length=150)
    telefono: str = Field(min_length=1, max_length=20)
    especialidad: str = Field(min_length=1, max_length=150)


class Guia(GuiaBase, table=True):
    __tablename__ = "guia"

    id_guia: Optional[int] = Field(
        default=None,
        primary_key=True
    )


class GuiaCreate(GuiaBase):
    pass


class GuiaUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(default=None, min_length=1, max_length=100)
    correo: Optional[str] = Field(default=None, min_length=1, max_length=150)
    telefono: Optional[str] = Field(default=None, min_length=1, max_length=20)
    especialidad: Optional[str] = Field(default=None, min_length=1, max_length=150)


class GuiaPublic(GuiaBase):
    id_guia: int
