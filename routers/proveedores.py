from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Session
from database import get_db, Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from routers.auth import get_usuario_actual

router = APIRouter()

class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(200))
    empresa = Column(String(200), nullable=False)
    telefono = Column(String(30))
    producto = Column(Text)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.now)

class ProveedorCreate(BaseModel):
    nombre: Optional[str] = None
    empresa: str
    telefono: Optional[str] = None
    producto: Optional[str] = None

@router.get("")
def listar(buscar: Optional[str] = None, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    q = db.query(Proveedor).filter(Proveedor.activo == True)
    if buscar:
        q = q.filter(Proveedor.empresa.ilike(f"%{buscar}%"))
    return q.order_by(Proveedor.creado_en.desc()).all()

@router.get("/{id}")
def obtener(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = db.query(Proveedor).filter(Proveedor.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return p

@router.post("")
def crear(datos: ProveedorCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = Proveedor(**datos.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.put("/{id}")
def editar(id: int, datos: ProveedorCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = db.query(Proveedor).filter(Proveedor.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in datos.dict().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p

@router.delete("/{id}")
def eliminar(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    p = db.query(Proveedor).filter(Proveedor.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="No encontrado")
    p.activo = False
    db.commit()
    return {"ok": True}
