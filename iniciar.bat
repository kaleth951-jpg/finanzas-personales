@echo off
title Fiskal - Servidor de Finanzas Personales
chcp 65001 >nul
cls

echo ==============================================================================
echo  💰 Fiskal - Servidor de Finanzas Personales ^& Machine Learning
echo ==============================================================================
echo.

set PYTHON_CMD=python

where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\laragon\bin\python\python-3.13\python.exe" (
        set PYTHON_CMD="C:\laragon\bin\python\python-3.13\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    )
)

echo [1/2] Verificando dependencias...
%PYTHON_CMD% -m pip install -q -r "%~dp0backend\requirements.txt" 2>nul

echo [2/2] Iniciando servidor Flask...
echo.
echo 🌐 Aplicación web disponible en: http://127.0.0.1:5000
echo.
echo Presiona Ctrl + C para detener el servidor en cualquier momento.
echo ==============================================================================
echo.

start http://127.0.0.1:5000
cd /d "%~dp0backend"
%PYTHON_CMD% app.py

pause
