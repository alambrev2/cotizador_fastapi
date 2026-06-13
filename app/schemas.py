from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from app.models import CustomerBase, QuoteBase, PaymentBase, AccountChargeBase, UserBase, RoleEnum


class CustomerCreate(CustomerBase):
    username: Optional[str] = None
    password: Optional[str] = None


class CustomerUpdate(SQLModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class Token(SQLModel):
    access_token: str
    token_type: str
    role: Optional[str] = None
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str

class CustomerShort(SQLModel):
    id: int
    nombre: str
    telefono: Optional[str] = None

class UserRead(UserBase):
    id: int
    cliente_vinculado: Optional[CustomerShort] = None

class UserAdminCreate(SQLModel):
    """Schema para que el Admin cree usuarios Operativos o Clientes."""
    username: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.Operativo
    is_active: bool = True
    cliente_id: Optional[int] = None

class UserUpdate(SQLModel):
    """Schema para editar un usuario existente (campos opcionales)."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None
    cliente_id: Optional[int] = None


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
    total_manual: Optional[Decimal] = None


class QuoteUpdate(SQLModel):
    estado: Optional[str] = None
    fecha_entrega: Optional[date] = None
    costo_compra_real: Optional[Decimal] = None
    costos_operativos: Optional[Decimal] = None


class QuotePublic(SQLModel):
    id: int
    fecha_creacion: str
    total: Decimal
    estado: str
    cliente_id: int


class QuoteItemRead(SQLModel):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal

class QuoteRead(QuoteBase):
    id: int
    fecha_creacion: datetime
    subtotal: Decimal = 0
    iva: Decimal = 0
    total: Decimal
    anticipo: Decimal = 0
    utilidad_total: Decimal = 0
    fecha_entrega: Optional[date] = None
    reporte_operativo_path: Optional[str] = None
    costo_compra_real: Optional[Decimal] = None
    costos_operativos: Decimal = 0
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
