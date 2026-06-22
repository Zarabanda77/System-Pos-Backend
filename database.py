import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Empaquetado como .exe: ignorar cualquier .env del disco y usar los
# valores por defecto del codigo (base de datos junto al ejecutable).
if not getattr(sys, "frozen", False):
    load_dotenv()


def base_dir():
    """Carpeta donde se guardan los datos (la base SQLite).

    - Empaquetado con PyInstaller: junto al .exe (escribible y persistente).
    - En desarrollo: la carpeta del proyecto backend.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_path = os.path.join(base_dir(), "tienda.db")
    DATABASE_URL = f"sqlite:///{db_path}"

# SQLite necesita check_same_thread=False para usarse con varios hilos (uvicorn).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
