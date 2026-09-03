# Fiskal - Script de Inicio en PowerShell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host " 💰 Fiskal - Servidor de Finanzas Personales & Machine Learning" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

$pythonCmd = $null
try {
    $test = & python -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = "python"
    }
} catch {}

if (-not $pythonCmd) {
    if (Test-Path "C:\laragon\bin\python\python-3.13\python.exe") {
        $pythonCmd = "C:\laragon\bin\python\python-3.13\python.exe"
    } elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe") {
        $pythonCmd = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    } elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe") {
        $pythonCmd = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    } elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe") {
        $pythonCmd = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    } elseif (Test-Path "C:\Program Files\Python313\python.exe") {
        $pythonCmd = "C:\Program Files\Python313\python.exe"
    } elseif (Test-Path "C:\Program Files\Python312\python.exe") {
        $pythonCmd = "C:\Program Files\Python312\python.exe"
    } else {
        $pythonCmd = "python"
    }
}

Write-Host "[1/2] Verificando dependencias..." -ForegroundColor Yellow
& $pythonCmd -m pip install -q -r "$PSScriptRoot\backend\requirements.txt"

Write-Host "[2/2] Iniciando servidor Flask..." -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Aplicación web disponible en: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Ctrl + C para detener el servidor en cualquier momento." -ForegroundColor Gray
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://127.0.0.1:5000"
Set-Location "$PSScriptRoot\backend"
& $pythonCmd app.py
