@echo off
cd /d "%~dp0"
echo ===================================================
echo   PromptBench Launcher - Database, Backend, UI
echo ===================================================
echo.
echo Select AI Evaluation Mode:
echo   [1] Live Gemini Mode  - Uses Google Gemini API
echo   [2] Offline Mock Mode - Local fallback for demos
echo.
set "MODE_CHOICE=1"
set /p "MODE_CHOICE=Enter 1 or 2 (Press Enter for 1): "

if "%MODE_CHOICE%"=="2" goto SET_MOCK

:SET_LIVE
echo.
echo [Config] Setting backend/.env to Live Gemini Mode (RUN_LLM_TESTS=true)...
powershell -NoProfile -Command "$f='backend\.env'; if (Test-Path $f) { (Get-Content $f) -replace '^RUN_LLM_TESTS=.*','RUN_LLM_TESTS=true' | Set-Content $f -Encoding UTF8 }"
goto LAUNCH

:SET_MOCK
echo.
echo [Config] Setting backend/.env to Offline Mock Mode (RUN_LLM_TESTS=false)...
powershell -NoProfile -Command "$f='backend\.env'; if (Test-Path $f) { (Get-Content $f) -replace '^RUN_LLM_TESTS=.*','RUN_LLM_TESTS=false' | Set-Content $f -Encoding UTF8 }"
goto LAUNCH

:LAUNCH
echo.
echo [1/3] Starting PostgreSQL...
if exist "scripts\start_postgres.bat" call "scripts\start_postgres.bat"
if exist "start_postgres.bat" call "start_postgres.bat"

echo.
echo [2/3] Launching FastAPI Backend on Port 8000...
if exist "scripts\start_backend.bat" start "PromptBench Backend" cmd /k "scripts\start_backend.bat"
if exist "start_backend.bat" start "PromptBench Backend" cmd /k "start_backend.bat"

echo.
echo [3/3] Launching React/Vite Frontend on Port 5173...
if exist "scripts\start_frontend.bat" start "PromptBench Frontend" cmd /k "scripts\start_frontend.bat"
if exist "start_frontend.bat" start "PromptBench Frontend" cmd /k "start_frontend.bat"

echo.
echo Waiting 4 seconds for servers to initialize...
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo.
echo ===================================================
echo   All services launched!
echo   Run .\stop_all.bat when you are ready to shut down.
echo ===================================================
