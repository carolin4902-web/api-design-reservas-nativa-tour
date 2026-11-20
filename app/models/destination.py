from typing import Optional
from sqlmodel import Field, SQLModel

# 1. Base compartida con los campos comunes
class DestinationBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: str
    location: str
    price_per_night: float
    max_guests: int = 4

# 2. La Tabla real de la Base de Datos
class Destination(DestinationBase, table=True):
    __tablename__ = "destinations"
    id: Optional[int] = Field(default=None, primary_key=True)

# 3. DTO para CREAR (Lo que envía el cliente por POST)
class DestinationCreate(DestinationBase):
    pass

# 4. DTO para ACTUALIZAR (Todos opcionales para PATCH)
class DestinationUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    price_per_night: Optional[float] = None
    max_guests: Optional[int] = None

# 5. DTO PÚBLICO (Lo que la API responde al cliente con su ID)
class DestinationPublic(DestinationBase):
    id: int