from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from app.models import CustomerBase, QuoteBase, PaymentBase, AccountChargeBase


class QuoteItemCreate(SQLModel):
    producto_id: int
    cantidad: int = Field(gt=0, description="La cantidad debe ser mayor a 0")
    precio_unitario: Decimal = Field(ge=0, description="Precio ajustado manualmente")


class QuoteCreate(SQLModel):
    cliente_id: int
    items: List[QuoteItemCreate]
    filial: Optional[str] = None
    agente: Optional[str] = None
    notas: Optional[str] = None
    requiere_factura: bool = False
    # Opcionales para financiamiento
    tipo_pago: str = "Contado"
    anticipo: Optional[Decimal] = 0
    fecha_inicio_pago: Optional[date] = None
    fecha_fin_pago: Optional[date] = None
    plazo_semanas: Optional[int] = 0
    monto_semanal: Optional[Decimal] = 0
    
    # Edición
    padre_id: Optional[int] = None
    motivo_edicion: Optional[str] = None


class QuoteUpdate(SQLModel):
    estado: Optional[str] = None
    fecha_entrega: Optional[date] = None
    costo_compra_real: Optional[float] = None
    costos_operativos: Optional[float] = None


class QuotePublic(SQLModel):
    id: int
    fecha_creacion: str
    total: float
    estado: str
    cliente_id: int


class QuoteItemRead(SQLModel):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: float

class QuoteRead(QuoteBase):
    id: int
    fecha_creacion: datetime
    subtotal: float = 0
    iva: float = 0
    total: float
    anticipo: float = 0
    utilidad_total: float = 0
    fecha_entrega: Optional[date] = None
    reporte_operativo_path: Optional[str] = None
    costo_compra_real: Optional[float] = None
    costos_operativos: float = 0
    cliente: Optional[CustomerBase] = None
    items: List[QuoteItemRead] = []


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: int


class AccountChargeCreate(AccountChargeBase):
    pass


class AccountChargeRead(AccountChargeBase):
    id: int
