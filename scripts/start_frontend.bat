@echo off
set "ROOT_DIR=%~dp0.."
echo Starting PromptBench React/Vite Frontend on http://localhost:5173...
cd /d "%ROOT_DIR%\frontend"
call npm.cmd run dev
