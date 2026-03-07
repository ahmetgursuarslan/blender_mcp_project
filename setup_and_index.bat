@echo off
echo ==============================================
echo Blender Expert MCP Server - Setup ^& Index API
echo ==============================================

if not exist venv\ (
    echo Creating python virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

echo Activating environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Running intelligent indexer...
echo Make sure html files exist in "blender_manual_html\" before proceeding for real results.
python src\indexer.py

echo.
echo Setup and Initial indexing complete!
pause
