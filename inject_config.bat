@echo off
echo ==============================================
echo Injecting MCP Server into IDE configurations...
echo ==============================================

if not exist venv\ (
    echo Warning: Virtual environment not found, ensuring global Python is used if needed.
) else (
    call venv\Scripts\activate.bat
)

python src\auto_config.py
pause
