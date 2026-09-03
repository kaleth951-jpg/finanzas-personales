@echo off
title Fiskal - Servidor de Finanzas Personales
chcp 65001 >nul
cls

echo ==============================================================================
echo   Fiskal - Servidor de Finanzas Personales ^& Machine Learning
echo ==============================================================================
echo.

set PYTHON_CMD=

REM 1. Probar si python del PATH es funcional
python -c "import sys" >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
)

REM 2. Si no funciona (ej. stub de WindowsApps), buscar en Laragon o AppData
if "%PYTHON_CMD%"=="" (
    if exist "C:\laragon\bin\python\python-3.13\python.exe" (
        set PYTHON_CMD="C:\laragon\bin\python\python-3.13\python.exe"
    )
)
if "%PYTHON_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    )
)
if "%PYTHON_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    )
)
if "%PYTHON_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    )
)
if "%PYTHON_CMD%"=="" (
    if exist "C:\Program Files\Python313\python.exe" (
        set PYTHON_CMD="C:\Program Files\Python313\python.exe"
    )
)
if "%PYTHON_CMD%"=="" (
    if exist "C:\Program Files\Python312\python.exe" (
        set PYTHON_CMD="C:\Program Files\Python312\python.exe"
    )
)
if "%PYTHON_CMD%"=="" (
    set PYTHON_CMD=python
)

echo [1/2] Verificando dependencias con %PYTHON_CMD%...
%PYTHON_CMD% -m pip install -q -r "%~dp0backend\requirements.txt" 2>nul

echo [2/2] Iniciando servidor Flask...
echo.
echo Aplicacion web disponible en: http://127.0.0.1:5000
echo.
echo Presiona Ctrl + C para detener el servidor en cualquier momento.
echo ==============================================================================
echo.

start http://127.0.0.1:5000
cd /d "%~dp0backend"
%PYTHON_CMD% app.py

pause
