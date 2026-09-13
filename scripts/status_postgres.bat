@echo off
set "ROOT_DIR=%~dp0.."
echo Checking PromptBench PostgreSQL Status...
if exist "%ROOT_DIR%\backend\venv\Scripts\python.exe" (
    "%ROOT_DIR%\backend\venv\Scripts\python.exe" "%ROOT_DIR%\backend\setup_postgres.py" status
) else (
    python "%ROOT_DIR%\backend\setup_postgres.py" status
)
