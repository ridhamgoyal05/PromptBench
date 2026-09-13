@echo off
set "ROOT_DIR=%~dp0.."
echo Stopping PromptBench PostgreSQL...
if exist "%ROOT_DIR%\backend\venv\Scripts\python.exe" (
    "%ROOT_DIR%\backend\venv\Scripts\python.exe" "%ROOT_DIR%\backend\setup_postgres.py" stop
) else (
    python "%ROOT_DIR%\backend\setup_postgres.py" stop
)
