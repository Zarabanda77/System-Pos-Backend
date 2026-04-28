from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Venta, DetalleVenta, Producto
from pydantic import BaseModel
from typing import Optional, List
from routers.auth import get_usuario_actual

router = APIRouter()

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
    cliente_id: Optional[int] = None
    es_credito: bool = False
    referencia_pago: Optional[str] = None
    nombre_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    detalles: List[DetalleVentaCreate]

@router.post("/")
def crear_venta(datos: VentaCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    from routers.clientes import Cliente, PagoVenta
    venta = Venta(
    subtotal=datos.subtotal,
    total=datos.total,
    metodo_pago=datos.metodo_pago,
    monto_recibido=datos.monto_recibido,
    cambio=datos.cambio,
    cliente_id=datos.cliente_id,
    es_credito=datos.es_credito,
    saldo_pendiente=datos.total if datos.es_credito else 0,
    referencia_pago=datos.referencia_pago,
    nombre_cliente=datos.nombre_cliente,
    telefono_cliente=datos.telefono_cliente
)
    db.add(venta)
    db.flush()

    for d in datos.detalles:
        detalle = DetalleVenta(venta_id=venta.id, **d.dict())
        db.add(detalle)
        producto = db.query(Producto).filter(Producto.id == d.producto_id).first()
        if producto:
            producto.stock_actual -= d.cantidad

    pago = PagoVenta(
        venta_id=venta.id,
        cliente_id=datos.cliente_id,
        metodo=datos.metodo_pago,
        monto=datos.total,
        referencia=datos.referencia_pago
    )
    db.add(pago)

    if datos.es_credito and datos.cliente_id:
        cliente = db.query(Cliente).filter(Cliente.id == datos.cliente_id).first()
        if cliente:
            cliente.saldo_credito += datos.total

    db.commit()
    db.refresh(venta)
    return venta

@router.get("/")
def listar_ventas(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    return db.query(Venta).order_by(Venta.fecha.desc()).limit(100).all()

@router.get("/{id}")
def obtener_venta(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    return db.query(Venta).filter(Venta.id == id).first()

@router.get("/historial/todas")
def todas_las_ventas(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    return db.query(Venta).order_by(Venta.fecha.desc()).limit(200).all()