from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Session
from database import get_db, Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from routers.auth import get_usuario_actual

router = APIRouter()

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    limite_credito = Column(Float, default=0)
    saldo_credito = Column(Float, default=0)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.now)

class PagoVenta(Base):
    __tablename__ = "pagos_venta"
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    metodo = Column(String(30), nullable=False)
    monto = Column(Float, nullable=False)
    referencia = Column(String(100))
    fecha = Column(DateTime, default=datetime.now)

class ClienteCreate(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    limite_credito: float = 0

class PagoCreate(BaseModel):
    venta_id: int
    cliente_id: Optional[int] = None
    metodo: str
    monto: float
    referencia: Optional[str] = None

@router.get("")
def listar(buscar: Optional[str] = None, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    q = db.query(Cliente).filter(Cliente.activo == True)
    if buscar:
        q = q.filter(Cliente.nombre.ilike(f"%{buscar}%"))
    return q.all()

@router.get("/{id}")
def obtener(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return c

@router.get("/{id}/historial")
def historial(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    from models import Venta
    ventas = db.query(Venta).filter(Venta.cliente_id == id)\
               .order_by(Venta.fecha.desc()).limit(20).all()
    return ventas

@router.post("")
def crear(datos: ClienteCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    c = Cliente(**datos.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.put("/{id}")
def editar(id: int, datos: ClienteCreate, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in datos.dict().items():
        setattr(c, k, v)
    db.commit()
    return c

@router.delete("/{id}")
def eliminar(id: int, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="No encontrado")
    c.activo = False
    db.commit()
    return {"ok": True}

@router.post("/{id}/abonar")
def abonar(id: int, monto: float, db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="No encontrado")
    if monto <= 0:
        raise HTTPException(status_code=400, detail="Monto inválido")
    c.saldo_credito = max(0, c.saldo_credito - monto)
    db.commit()
    return {"saldo_nuevo": c.saldo_credito}