from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Producto, MovimientoInventario
from schemas import MovimientoCreate
from routers.auth import get_usuario_actual

router = APIRouter()

@router.post("/movimiento")
def registrar_movimiento(datos: MovimientoCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    producto = db.query(Producto).filter(Producto.id == datos.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    stock_anterior = producto.stock_actual
    if datos.tipo == "entrada":
        producto.stock_actual += datos.cantidad
    elif datos.tipo == "salida":
        producto.stock_actual -= datos.cantidad
    elif datos.tipo == "ajuste":
        producto.stock_actual = datos.cantidad
    mov = MovimientoInventario(
        producto_id=datos.producto_id,
        tipo=datos.tipo,
        cantidad=datos.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=producto.stock_actual,
        motivo=datos.motivo
    )
    db.add(mov)
    db.commit()
    return {"stock_nuevo": producto.stock_actual}

@router.get("/stock-bajo")
def stock_bajo(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    return db.query(Producto).filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    ).all()