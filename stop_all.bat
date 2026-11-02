@echo off
cd /d "%~dp0"
echo ===================================================
echo   Stopping PromptBench Services Safely
echo ===================================================

echo.
echo [1/3] Stopping Frontend Server (Port 5173)...
taskkill /FI "WINDOWTITLE eq PromptBench Frontend*" /T /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /T /F >nul 2>&1
)

echo [2/3] Stopping FastAPI Backend Server (Port 8000)...
taskkill /FI "WINDOWTITLE eq PromptBench Backend*" /T /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /T /F >nul 2>&1
)

echo [3/3] Stopping PostgreSQL Database...
if exist "scripts\stop_postgres.bat" (
    call "scripts\stop_postgres.bat"
) else if exist "stop_postgres.bat" (
    call "stop_postgres.bat"
)

echo.
echo ===================================================
echo   All PromptBench services have been stopped cleanly!
echo ===================================================
