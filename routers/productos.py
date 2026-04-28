from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Producto
from schemas import ProductoCreate
from typing import Optional
from routers.auth import get_usuario_actual

router = APIRouter()

@router.get("/barcode/{codigo}")
def buscar_por_barcode(codigo: str, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = db.query(Producto).filter(Producto.codigo_barras == codigo, Producto.activo == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return p

@router.get("/")
def listar(buscar: Optional[str] = None, categoria_id: Optional[int] = None, stock_bajo: bool = False, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    q = db.query(Producto).filter(Producto.activo == True)
    if buscar:
        q = q.filter(Producto.nombre.ilike(f"%{buscar}%"))
    if categoria_id:
        q = q.filter(Producto.categoria_id == categoria_id)
    if stock_bajo:
        q = q.filter(Producto.stock_actual <= Producto.stock_minimo)
    return q.all()

@router.get("/{id}")
def obtener(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="No encontrado")
    return p

@router.post("/")
def crear(datos: ProductoCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = Producto(**datos.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.put("/{id}")
def editar(id: int, datos: ProductoCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in datos.dict().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p

@router.delete("/{id}")
def eliminar(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="No encontrado")
    p.activo = False
    db.commit()
    return {"ok": True}