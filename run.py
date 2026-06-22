"""Punto de entrada para el ejecutable (.exe) de la Tienda.

Arranca el servidor web local y abre el navegador automaticamente.
Todo corre en la PC del cliente, sin internet.
"""
import threading
import time
import webbrowser

import uvicorn

from main import app

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://localhost:{PORT}"


def abrir_navegador():
    time.sleep(2)
    webbrowser.open(URL)


if __name__ == "__main__":
    print("=" * 50)
    print("  SISTEMA TIENDA")
    print(f"  Abriendo en: {URL}")
    print("  Para cerrar el programa, cierra esta ventana.")
    print("=" * 50)
    threading.Thread(target=abrir_navegador, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, loop="asyncio", http="h11", log_level="info")
