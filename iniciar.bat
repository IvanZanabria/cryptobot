@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM ===== Configuracion de MySQL (XAMPP). Cambia estos valores si hace falta =====
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=
set DB_NAME=cryptobot
REM ==============================================================================

set PY=python
where python >nul 2>nul || set PY=py

if not exist .venv (
    echo Creando entorno virtual...
    %PY% -m venv .venv
)
call .venv\Scripts\activate.bat

echo Instalando dependencias (la primera vez tarda un poco)...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

python setup_db.py
if errorlevel 1 (
    pause
    exit /b 1
)

REM Abre el navegador unos segundos despues, cuando el servidor ya este arriba
start "" cmd /c "timeout /t 8 >nul & start http://localhost:5000"

echo.
echo Sistema iniciando... cierra esta ventana o presiona Ctrl+C para detener todo.
python run_all.py 2
pause
