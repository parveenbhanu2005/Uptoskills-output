@echo off
SETLOCAL EnableDelayedExpansion

:: Get the directory of the batch file
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo ===================================================
echo   Solar Panel Inspection Platform Auto-Runner
echo ===================================================
echo.
echo Project Directory: %PROJECT_DIR%
echo.

:: Check for node_modules and install if not present
if not exist "node_modules\" (
    echo [INFO] node_modules not found. Installing frontend dependencies...
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] npm install failed. Please check your Node.js installation.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Frontend dependencies are already installed.
)

:: Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in system PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: Verify Node installation
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in system PATH.
    echo Please install Node.js and try again.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting FastAPI Backend on port 8000...
start "SolarLens FastAPI Backend" cmd /k "title SolarLens FastAPI Backend && cd /d "%PROJECT_DIR%" && python -m backend.main"

echo [INFO] Starting Frontend/Express Server on port 3000...
start "SolarLens Frontend" cmd /k "title SolarLens Frontend && cd /d "%PROJECT_DIR%" && npm run dev"

echo.
echo ===================================================
echo   Services are starting up...
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:3000
echo ===================================================
echo.
echo You can close this main window. The servers will keep running in their respective windows.
echo.
pause
