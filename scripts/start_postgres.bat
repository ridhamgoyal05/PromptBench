@echo off
set "ROOT_DIR=%~dp0.."
echo Starting PromptBench PostgreSQL on localhost:5432...
if exist "%ROOT_DIR%\backend\venv\Scripts\python.exe" (
    "%ROOT_DIR%\backend\venv\Scripts\python.exe" "%ROOT_DIR%\backend\setup_postgres.py" start
) else (
    python "%ROOT_DIR%\backend\setup_postgres.py" start
)
