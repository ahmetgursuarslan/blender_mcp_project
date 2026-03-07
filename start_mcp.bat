@echo off
if not exist venv\ (
    echo Error: Virtual environment "venv" not found. Please run setup_and_index.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python src\mcp_server.py
