@echo off
set "ROOT_DIR=%~dp0.."
echo Starting PromptBench FastAPI Backend on http://localhost:8000...
cd /d "%ROOT_DIR%"
if exist "%ROOT_DIR%\backend\venv\Scripts\python.exe" (
    "%ROOT_DIR%\backend\venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
)
