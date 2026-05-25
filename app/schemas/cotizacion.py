from pydantic import BaseModel


class CotizacionBase(BaseModel):
    cliente: str
    producto: str
    cantidad: int
    precio_unitario: float


class CotizacionCreate(CotizacionBase):
    pass


class Cotizacion(CotizacionBase):
    id: int
    total: float

    class Config:
        from_attributes = True
