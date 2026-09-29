@echo off
REM ============================================================
REM First-Time Setup Script for Building Executable
REM This script prepares the environment for building the .exe
REM ============================================================

echo ============================================================
echo Row Inspection Application - Build Environment Setup
echo ============================================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Found Python
python --version
echo.

REM Check pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)

echo.
echo Updating pip...
python -m pip install --upgrade pip --quiet

echo.
echo Installing build dependencies...
python -m pip install pyinstaller --quiet

echo.
echo Installing application dependencies...
python -m pip install -r requirements_exe.txt --quiet

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo You can now build the executable by running:
echo   build_simple.bat
echo.
echo Or for a more controlled build:
echo   build_exe.bat
echo.
echo Note: If you use a virtual environment, make sure it's
echo activated before running the build script.
echo.
pause