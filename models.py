from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True)
    codigo_barras = Column(String(50), unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    precio_unitario = Column(Float, default=0)
    precio_por_kilo = Column(Float, nullable=True)
    costo = Column(Float, default=0)
    es_por_peso = Column(Boolean, default=False)
    stock_actual = Column(Float, default=0)
    stock_minimo = Column(Float, default=0)
    unidad_medida = Column(String(20), default="unidad")
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.now)
    categoria = relationship("Categoria", back_populates="productos")

class Venta(Base):
    __tablename__ = "ventas"
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.now)
    subtotal = Column(Float)
    total = Column(Float)
    metodo_pago = Column(String(20), default="efectivo")
    monto_recibido = Column(Float)
    cambio = Column(Float)
    estado = Column(String(20), default="completada")
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    es_credito = Column(Boolean, default=False)
    saldo_pendiente = Column(Float, default=0)
    referencia_pago = Column(String(100), nullable=True)
    detalles = relationship("DetalleVenta", back_populates="venta") 
    nombre_cliente = Column(String(200), nullable=True)
    telefono_cliente = Column(String(20), nullable=True)

class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    nombre_producto = Column(String(200))
    cantidad = Column(Float)
    precio_unitario = Column(Float)
    subtotal = Column(Float)
    venta = relationship("Venta", back_populates="detalles")

class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    tipo = Column(String(20), nullable=False)
    cantidad = Column(Float)
    stock_anterior = Column(Float)
    stock_nuevo = Column(Float)
    motivo = Column(Text)
    fecha = Column(DateTime, default=datetime.now)