from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductoBase(BaseModel):
    codigo_barras: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None
    precio_unitario: float = 0
    precio_por_kilo: Optional[float] = None
    costo: float = 0
    es_por_peso: bool = False
    stock_actual: float = 0
    stock_minimo: float = 0
    unidad_medida: str = "unidad"

class ProductoCreate(ProductoBase):
    pass

class ProductoOut(ProductoBase):
    id: int
    activo: bool
    creado_en: datetime
    class Config:
        from_attributes = True

class DetalleVentaCreate(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: float
    precio_unitario: float
    subtotal: float

class VentaCreate(BaseModel):
    subtotal: float
    total: float
    metodo_pago: str = "efectivo"
    monto_recibido: Optional[float] = None
    cambio: Optional[float] = None
    detalles: list[DetalleVentaCreate]

class MovimientoCreate(BaseModel):
    producto_id: int
    tipo: str
    cantidad: float
    motivo: Optional[str] = None