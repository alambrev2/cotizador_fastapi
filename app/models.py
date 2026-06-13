from typing import Optional, List
from datetime import datetime, date
from sqlmodel import Field, SQLModel, Relationship
from decimal import Decimal
from pydantic import EmailStr
from enum import Enum

class RoleEnum(str, Enum):
    Administrador = "Administrador"
    Operativo = "Operativo"
    Cliente = "Cliente"

# --- Modelos Base ---


class CustomerBase(SQLModel):
    nombre: str = Field(min_length=1, nullable=False, description="El nombre no puede estar vacío")
    email: EmailStr = Field(unique=True, index=True, nullable=False)
    telefono: Optional[str] = None
    direccion: Optional[str] = None

    # Campos Históricos / Financieros
    saldo_inicial: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    consumo_2022: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    consumo_2023: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    consumo_2024: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    consumo_2025: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    consumo_2026: Decimal = Field(default=0, max_digits=10, decimal_places=2)


class ProductBase(SQLModel):
    nombre: str = Field(min_length=1, nullable=False)
    descripcion: Optional[str] = None
    marca: Optional[str] = None
    costo: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    categoria: Optional[str] = None
    proveedor: Optional[str] = None
    stock_minimo: int = Field(default=5, ge=0)
    unidad_medida: str = Field(default="Pieza")
    precio_menudeo: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    precio_mayoreo: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    cantidad_mayoreo: int = Field(
        default=16, description="Cantidad mínima para aplicar precio mayoreo", gt=0
    )
    stock: int = Field(default=0, description="Inventario actual", ge=0)
    activo: bool = Field(default=True, nullable=False)


class ExpenseBase(SQLModel):
    descripcion: str = Field(min_length=1, nullable=False)
    monto: Decimal = Field(default=0, max_digits=10, decimal_places=2, gt=0)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    categoria: Optional[str] = "Gasto General"


class QuoteBase(SQLModel):
    estado: str = "Borrador"  # Borrador, Enviada, Aceptada, Rechazada
    cliente_id: Optional[int] = Field(default=None, foreign_key="customer.id")

    # Contabilidad e Impuestos
    requiere_factura: bool = Field(default=False)
    subtotal: Optional[Decimal] = Field(default=0, max_digits=10, decimal_places=2)
    iva: Optional[Decimal] = Field(default=0, max_digits=10, decimal_places=2)

    # Metadatos del Vendedor
    filial: Optional[str] = None
    agente: Optional[str] = None
    notas: Optional[str] = None

    # Campos de Financiamiento
    tipo_pago: str = Field(default="Contado")  # Contado, 2 Pagos, Semanal
    anticipo: Optional[Decimal] = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    fecha_inicio_pago: Optional[date] = None
    fecha_fin_pago: Optional[date] = None
    plazo_semanas: Optional[int] = Field(default=0)
    monto_semanal: Optional[Decimal] = Field(default=0, max_digits=10, decimal_places=2)

    # Trazabilidad y Versiones
    folio_cotizacion: Optional[str] = Field(default=None, unique=True)
    padre_id: Optional[int] = Field(default=None, foreign_key="quote.id")
    motivo_edicion: Optional[str] = Field(default=None)
    version: int = Field(default=1)
    utilidad_total: Optional[Decimal] = Field(default=0, max_digits=10, decimal_places=2)

    # Proyectos Aprobados (Operación)
    fecha_entrega: Optional[date] = None
    reporte_operativo_path: Optional[str] = None
    costo_compra_real: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    costos_operativos: Optional[Decimal] = Field(default=0, max_digits=10, decimal_places=2)


class QuoteItemBase(SQLModel):
    producto_id: Optional[int] = Field(default=None, foreign_key="product.id", nullable=False)
    cantidad: int = Field(default=1, gt=0)
    precio_unitario: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)


class PaymentBase(SQLModel):
    monto: Decimal = Field(default=0, max_digits=10, decimal_places=2, gt=0)
    fecha_pago: datetime = Field(default_factory=datetime.utcnow)
    metodo_pago: str = "Transferencia"  # Efectivo, Transferencia, Tarjeta
    referencia: Optional[str] = None
    nota: Optional[str] = None
    quote_id: Optional[int] = Field(default=None, foreign_key="quote.id")
    cargo_id: Optional[int] = Field(default=None, foreign_key="accountcharge.id")
    cliente_id: Optional[int] = Field(default=None, foreign_key="customer.id")


class AccountChargeBase(SQLModel):
    detalle: str = Field(min_length=1, nullable=False)
    monto: Decimal = Field(default=0, max_digits=10, decimal_places=2, gt=0)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    documentado: bool = Field(default=False)
    cliente_id: Optional[int] = Field(default=None, foreign_key="customer.id")
    folio_nota: Optional[str] = Field(default=None)
    estatus: str = Field(default="Pendiente")


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, nullable=False)
    email: EmailStr = Field(unique=True, index=True, nullable=False)
    role: RoleEnum = Field(default=RoleEnum.Cliente)
    is_active: bool = Field(default=True)
    cliente_id: Optional[int] = Field(default=None, foreign_key="customer.id")


# --- Modelos de Tabla ---


class Customer(CustomerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    cotizaciones: List["Quote"] = Relationship(back_populates="cliente")
    pagos: List["Payment"] = Relationship(back_populates="cliente")
    cargos: List["AccountCharge"] = Relationship(back_populates="cliente")
    usuarios: List["User"] = Relationship(back_populates="cliente_vinculado")


class AccountCharge(AccountChargeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente: Optional[Customer] = Relationship(back_populates="cargos")
    pagos: List["Payment"] = Relationship(back_populates="cargo")


class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class Quote(QuoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    total: Decimal = Field(default=0, max_digits=10, decimal_places=2)

    cliente: Optional[Customer] = Relationship(back_populates="cotizaciones")
    items: List["QuoteItem"] = Relationship(back_populates="cotizacion")
    pagos: List["Payment"] = Relationship(back_populates="cotizacion")


class QuoteItem(QuoteItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cotizacion_id: Optional[int] = Field(default=None, foreign_key="quote.id")

    cotizacion: Optional[Quote] = Relationship(back_populates="items")
    producto: Optional["Product"] = Relationship()


class Payment(PaymentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    cotizacion: Optional[Quote] = Relationship(back_populates="pagos")
    cliente: Optional[Customer] = Relationship(back_populates="pagos")
    cargo: Optional[AccountCharge] = Relationship(back_populates="pagos")


class Expense(ExpenseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class OtherIncomeBase(SQLModel):
    descripcion: str
    monto: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    categoria: Optional[str] = "Ingreso General"


class OtherIncome(OtherIncomeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ServicePaymentBase(SQLModel):
    servicio: str = Field(min_length=1, nullable=False, description='Nombre del servicio')
    monto_estimado: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    fecha_vencimiento: date = Field(nullable=False)
    estado: str = Field(default='Pendiente') # Pendiente, Pagado, Vencido
    monto_pagado: Optional[Decimal] = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    fecha_pago: Optional[date] = None
    referencia: Optional[str] = None
    notas: Optional[str] = None

class ServicePayment(ServicePaymentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ScheduledExpenseBase(SQLModel):
    descripcion: str = Field(min_length=1, nullable=False)
    monto: Decimal = Field(default=0, max_digits=10, decimal_places=2, gt=0)
    fecha_vencimiento: date = Field(nullable=False)
    categoria: Optional[str] = Field(default='General')
    clabe: Optional[str] = None
    estatus: str = Field(default='Pendiente') # Pendiente / Pagado
    frecuencia: str = Field(default='Único') # Único, Mensual, Bimestral, Semestral, Anual

class ScheduledExpense(ScheduledExpenseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)
    magic_token: Optional[str] = Field(default=None, unique=True, index=True)
    magic_token_expires: Optional[datetime] = Field(default=None)

    cliente_vinculado: Optional[Customer] = Relationship(back_populates="usuarios")

