@echo off
REM ============================================================
REM   COMPILAR TIENDA  ->  genera el Tienda.exe NUEVO
REM   (con los ultimos cambios) para entregarselo al cliente.
REM
REM   COMO USARLO:  doble clic en este archivo.
REM   Al terminar, el ejecutable queda en:   dist\Tienda.exe
REM   Eso es lo unico que le pasas al cliente.
REM ============================================================
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================================
echo   COMPILANDO TIENDA  (esto puede tardar unos minutos)
echo ============================================================

REM --- Verificacion: que exista el entorno virtual ---
if not exist "venv\Scripts\python.exe" (
  echo.
  echo ERROR: no se encuentra el entorno virtual ^(venv^).
  echo Crea el venv e instala requirements.txt antes de compilar.
  echo.
  pause & exit /b 1
)

REM --- Verificacion: que exista el proyecto frontend ---
if not exist "..\tienda-frontend\package.json" (
  echo.
  echo ERROR: no se encuentra ..\tienda-frontend
  echo Asegurate de que las carpetas tienda-backend y tienda-frontend
  echo esten juntas en la misma ubicacion.
  echo.
  pause & exit /b 1
)

REM --- Aviso si el programa esta abierto (bloquearia el .exe) ---
if exist "dist\Tienda.exe" (
  echo.
  echo Si tienes el programa Tienda ABIERTO, cierralo antes de continuar.
  echo.
  pause
)

echo.
echo [1/4] Compilando el frontend ^(Angular, modo produccion^)...
pushd "..\tienda-frontend"
call npm run build
if errorlevel 1 ( echo ERROR compilando el frontend & popd & pause & exit /b 1 )
popd

echo.
echo [2/4] Copiando el frontend al backend...
if exist "frontend" rmdir /s /q "frontend"
mkdir "frontend"
xcopy "..\tienda-frontend\dist\tienda-frontend\browser\*" "frontend\" /e /i /y >nul
if errorlevel 1 ( echo ERROR copiando el frontend & pause & exit /b 1 )

echo.
echo [3/4] Limpiando compilacion anterior...
if exist "build" rmdir /s /q "build"

echo.
echo [4/4] Empaquetando el ejecutable ^(PyInstaller^)...
call "venv\Scripts\python.exe" -m PyInstaller --onefile --name Tienda ^
  --add-data "frontend;frontend" ^
  --collect-all uvicorn --collect-all passlib --collect-all jose ^
  --hidden-import bcrypt --noconfirm run.py
if errorlevel 1 (
  echo.
  echo ERROR empaquetando. Causa mas comun: el programa Tienda estaba abierto.
  echo Cierralo y vuelve a ejecutar este compilar.bat.
  echo.
  pause & exit /b 1
)

echo.
echo ============================================================
echo   LISTO. Entrega este archivo al cliente:
echo.
echo       %~dp0dist\Tienda.exe
echo.
echo   El cliente solo reemplaza su Tienda.exe viejo por este.
echo   Su archivo tienda.db ^(datos^) NO se toca.
echo ============================================================
echo.
if exist "dist\Tienda.exe" explorer "dist"
pause
