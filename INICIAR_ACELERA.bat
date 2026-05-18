@echo off
setlocal

set "ROOT=%~dp0"
set "API_DIR=%ROOT%API"
set "FRONTEND_DIR=%ROOT%FRONTEND"
set "API_PYTHON=%API_DIR%\.venv\Scripts\python.exe"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

if exist "%API_PYTHON%" (
  set "PYTHON_CMD=%API_PYTHON%"
) else (
  set "PYTHON_CMD=python"
)

start "Acelera API" /min cmd /k "cd /d "%API_DIR%" && "%PYTHON_CMD%" -m uvicorn main:app --host 127.0.0.1 --port 8000"
start "Acelera Frontend" /min cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev -- --host 127.0.0.1"

timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5173"

endlocal
