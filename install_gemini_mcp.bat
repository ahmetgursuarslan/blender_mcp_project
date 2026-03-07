@echo off
echo ===================================================
echo     Gemini CLI - MCP Server Injector
echo ===================================================

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run setup_and_index.bat first.
    pause
    exit /b
)

echo Injecting Blender Expert MCP into Gemini CLI configuration...
"venv\Scripts\python.exe" "src\cli_injector.py" gemini

echo ===================================================
pause
