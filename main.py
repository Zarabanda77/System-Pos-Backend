import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from database import engine, Base, SessionLocal
from routers import productos, ventas, inventario, reportes, auth, bodegas, clientes, proveedores
from routers.clientes import Cliente, PagoVenta
from routers.bodegas import Bodega, StockBodega
from routers.proveedores import Proveedor
from routers.auth import Usuario, pwd_context
from dotenv import load_dotenv

if not getattr(sys, "frozen", False):
    load_dotenv()

Base.metadata.create_all(bind=engine)


def bundle_dir():
    """Carpeta de recursos empaquetados (solo lectura).

    - Con PyInstaller: la carpeta temporal donde se extrae el bundle.
    - En desarrollo: la carpeta del proyecto backend.
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


FRONTEND_DIR = os.path.join(bundle_dir(), "frontend")


def crear_admin_inicial():
    """Crea un usuario administrador la primera vez (base de datos vacía)."""
    db = SessionLocal()
    try:
        if not db.query(Usuario).first():
            admin = Usuario(
                nombre="Administrador",
                email="admin@tienda.com",
                password_hash=pwd_context.hash("admin123"),
                rol="admin",
                activo=True,
            )
            db.add(admin)
            db.commit()
            print(">> Usuario inicial creado: admin@tienda.com / admin123")
    finally:
        db.close()


app = FastAPI(title="Sistema Tienda", version="1.0")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
def on_startup():
    crear_admin_inicial()


app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(productos.router,   prefix="/api/productos",   tags=["Productos"])
app.include_router(ventas.router,      prefix="/api/ventas",      tags=["Ventas"])
app.include_router(inventario.router,  prefix="/api/inventario",  tags=["Inventario"])
app.include_router(bodegas.router,     prefix="/api/bodegas",     tags=["Bodegas"])
app.include_router(reportes.router,    prefix="/api/reportes",    tags=["Reportes"])
app.include_router(clientes.router,    prefix="/api/clientes",    tags=["Clientes"])
app.include_router(proveedores.router, prefix="/api/proveedores", tags=["Proveedores"])


@app.get("/api")
def api_root():
    return {"mensaje": "API Tienda funcionando"}


# --- Servir el frontend Angular compilado (SPA) ---
# Cualquier ruta que no sea /api se resuelve contra los archivos del frontend.
# Si el archivo no existe (rutas internas de Angular), se devuelve index.html.
@app.get("/{full_path:path}")
def servir_frontend(full_path: str):
    # No servir el frontend para rutas de API desconocidas: devolver 404 real.
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Ruta de API no encontrada")
    archivo = os.path.join(FRONTEND_DIR, full_path)
    if full_path and os.path.isfile(archivo):
        return FileResponse(archivo)
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return {"error": "Frontend no encontrado. ¿Compilaste el Angular en la carpeta 'frontend'?"}
