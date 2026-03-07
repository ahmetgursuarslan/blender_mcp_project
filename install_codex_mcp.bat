@echo off
echo ===================================================
echo     Codex CLI - MCP Server Injector
echo ===================================================

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run setup_and_index.bat first.
    pause
    exit /b
)

echo Injecting Blender Expert MCP into Codex CLI configuration...
"venv\Scripts\python.exe" "src\cli_injector.py" codex

echo ===================================================
pause
