from sqlmodel import Field, SQLModel

class Tour(SQLModel, table=True):
    id_tour: int | None = Field(default=None, primary_key=True)
    nombre: str
    descripcion: str
    ubicacion: str
    precio: float
    capacidad: int
    id_guia: int = Field(foreign_key="guia.id_guia")
    
