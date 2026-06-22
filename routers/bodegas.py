from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Session, relationship
from database import get_db, Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from routers.auth import get_usuario_actual

router = APIRouter()

class Bodega(Base):
    __tablename__ = "bodegas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.now)

class StockBodega(Base):
    __tablename__ = "stock_bodegas"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    bodega_id = Column(Integer, ForeignKey("bodegas.id"))
    stock_actual = Column(Float, default=0)
    stock_minimo = Column(Float, default=0)

class StockUpdate(BaseModel):
    producto_id: int
    bodega_id: int
    stock_actual: float
    stock_minimo: Optional[float] = 0

class TransferenciaCreate(BaseModel):
    producto_id: int
    bodega_origen_id: int
    bodega_destino_id: int
    cantidad: float

# Listar bodegas
@router.get("")
def listar_bodegas(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    return db.query(Bodega).filter(Bodega.activo == True).all()

# Stock de un producto en todas las bodegas
@router.get("/stock/{producto_id}")
def stock_por_producto(producto_id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    stocks = db.query(StockBodega).filter(
        StockBodega.producto_id == producto_id
    ).all()
    bodegas = db.query(Bodega).all()
    resultado = []
    for bodega in bodegas:
        stock = next((s for s in stocks if s.bodega_id == bodega.id), None)
        resultado.append({
            "bodega_id": bodega.id,
            "bodega": bodega.nombre,
            "stock_actual": stock.stock_actual if stock else 0,
            "stock_minimo": stock.stock_minimo if stock else 0
        })
    return resultado

# Stock total de todos los productos por bodega
@router.get("/inventario/{bodega_id}")
def inventario_bodega(bodega_id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    from models import Producto
    stocks = db.query(StockBodega, Producto).join(
        Producto, StockBodega.producto_id == Producto.id
    ).filter(StockBodega.bodega_id == bodega_id).all()
    return [{
        "producto_id": p.id,
        "nombre": p.nombre,
        "codigo_barras": p.codigo_barras,
        "stock_actual": s.stock_actual,
        "stock_minimo": s.stock_minimo,
        "alerta": s.stock_actual <= s.stock_minimo
    } for s, p in stocks]

# Actualizar stock en una bodega
@router.post("/stock")
def actualizar_stock(datos: StockUpdate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    stock = db.query(StockBodega).filter(
        StockBodega.producto_id == datos.producto_id,
        StockBodega.bodega_id == datos.bodega_id
    ).first()
    if stock:
        stock.stock_actual = datos.stock_actual
        stock.stock_minimo = datos.stock_minimo
    else:
        stock = StockBodega(**datos.dict())
        db.add(stock)
    db.commit()
    return {"ok": True, "stock_actual": datos.stock_actual}

# Transferir entre bodegas
@router.post("/transferir")
def transferir(datos: TransferenciaCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    origen = db.query(StockBodega).filter(
        StockBodega.producto_id == datos.producto_id,
        StockBodega.bodega_id == datos.bodega_origen_id
    ).first()
    if not origen or origen.stock_actual < datos.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente en bodega origen")
    destino = db.query(StockBodega).filter(
        StockBodega.producto_id == datos.producto_id,
        StockBodega.bodega_id == datos.bodega_destino_id
    ).first()
    origen.stock_actual -= datos.cantidad
    if destino:
        destino.stock_actual += datos.cantidad
    else:
        db.add(StockBodega(
            producto_id=datos.producto_id,
            bodega_id=datos.bodega_destino_id,
            stock_actual=datos.cantidad
        ))
    db.commit()
    return {"ok": True, "mensaje": f"Transferidos {datos.cantidad} unidades"}