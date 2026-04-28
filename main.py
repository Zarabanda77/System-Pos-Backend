import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import productos, ventas, inventario, reportes, auth, bodegas, clientes
from routers.clientes import Cliente, PagoVenta
from routers.bodegas import Bodega, StockBodega
from routers.auth import Usuario
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema Tienda", version="1.0")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(productos.router,   prefix="/api/productos",   tags=["Productos"])
app.include_router(ventas.router,      prefix="/api/ventas",      tags=["Ventas"])
app.include_router(inventario.router,  prefix="/api/inventario",  tags=["Inventario"])
app.include_router(bodegas.router,     prefix="/api/bodegas",     tags=["Bodegas"])
app.include_router(reportes.router,    prefix="/api/reportes",    tags=["Reportes"])
app.include_router(clientes.router,    prefix="/api/clientes",    tags=["Clientes"])

@app.get("/")
def root():
    return {"mensaje": "API Tienda funcionando"}