@echo off
echo ===================================================
echo     Elite MCP Bridge - Installation Script
echo ===================================================

set "BLENDER_ADDONS=%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons"

if not exist "%BLENDER_ADDONS%" (
    echo [INFO] Blender 5.0 addons directory not found. Creating it...
    mkdir "%BLENDER_ADDONS%"
)

echo [INFO] Installing Elite MCP Bridge v3.0 to "%BLENDER_ADDONS%\elite_mcp_bridge_v3"...
xcopy /E /I /Y "src\bridge" "%BLENDER_ADDONS%\elite_mcp_bridge_v3"

echo.
echo [SUCCESS] Add-on installed successfully!
echo.
echo ===================================================
echo   NEXT STEPS TO ACTIVATE THE BRIDGE IN BLENDER
echo ===================================================
echo 1. Open Blender 5.0
echo 2. Go to Edit -^> Preferences -^> Add-ons
echo 3. Search for "Elite MCP Bridge v3"
echo 4. Check the box to enable it
echo.
echo The background bridge will start automatically
echo and write its secure token to ~/.blender_mcp_lock
echo ===================================================
pause
