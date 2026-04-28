from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Venta, DetalleVenta, Producto
from datetime import datetime, timedelta, timezone
from routers.auth import get_usuario_actual

router = APIRouter()

@router.get("/hoy")
def ventas_hoy(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    ahora = datetime.now()
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_hoy = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)
    ventas = db.query(Venta).filter(
        Venta.fecha >= inicio_hoy,
        Venta.fecha <= fin_hoy,
        Venta.estado == "completada"
    ).all()
    total = sum(v.total for v in ventas) if ventas else 0
    return {
        "fecha": str(ahora.date()),
        "cantidad_ventas": len(ventas),
        "total": total
    }
    
    
@router.get("/semana")
def ventas_semana(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    hace7 = datetime.now() - timedelta(days=7)
    ventas = db.query(Venta).filter(
        Venta.fecha >= hace7,
        Venta.estado == "completada"
    ).all()
    total = sum(v.total for v in ventas)
    return {"cantidad_ventas": len(ventas), "total": total}

@router.get("/productos-mas-vendidos")
def mas_vendidos(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    resultado = db.query(
        DetalleVenta.nombre_producto,
        func.sum(DetalleVenta.cantidad).label("total_vendido"),
        func.sum(DetalleVenta.subtotal).label("total_ingresos")
    ).group_by(DetalleVenta.nombre_producto)\
     .order_by(func.sum(DetalleVenta.cantidad).desc())\
     .limit(10).all()
    return [{"producto": r[0], "cantidad": r[1], "ingresos": r[2]} for r in resultado]

@router.get("/metodos-pago")
def metodos_pago(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    resultado = db.query(
        Venta.metodo_pago,
        func.sum(Venta.total).label("total")
    ).filter(Venta.estado == "completada")\
     .group_by(Venta.metodo_pago).all()
    return [{"metodo": r[0], "total": r[1]} for r in resultado]

@router.get("/ventas-por-dia")
def ventas_por_dia(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    hace7 = datetime.now() - timedelta(days=7)
    resultado = db.query(
        func.date(Venta.fecha).label("dia"),
        func.sum(Venta.total).label("total")
    ).filter(
        Venta.fecha >= hace7,
        Venta.estado == "completada"
    ).group_by(func.date(Venta.fecha))\
     .order_by(func.date(Venta.fecha)).all()
    return [{"dia": str(r[0]), "total": r[1]} for r in resultado]