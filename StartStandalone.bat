@echo off
title Standalone Startup
color 07

REM ============================================
REM Standalone and Airflow Services Startup
REM Version: 2.0
REM Last Updated: 2026-09-17
REM ============================================

echo =====================================================
echo        Starting Standalone and Airflow Services
echo =====================================================
echo.

REM -------------------------------------------
REM Step 1: Check Docker Installation
REM -------------------------------------------
echo [1/5] Checking Docker Installation in WSL...
echo.

wsl -d Ubuntu -- bash -c "docker --version > /dev/null 2>&1"
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH within WSL Ubuntu.
    echo [INFO] Please install Docker Engine in WSL Ubuntu:
    echo        1. Open WSL: wsl -d Ubuntu
    echo        2. Follow Docker installation guide for Ubuntu
    echo        3. Ensure docker service is running
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is installed in WSL Ubuntu.
echo.

REM -------------------------------------------
REM Step 2: Check Docker Engine Status
REM -------------------------------------------
echo [2/5] Checking Docker Engine Status...
echo.

wsl -d Ubuntu -- bash -c "docker info > /dev/null 2>&1"

if %errorlevel% neq 0 (
    echo [WARNING] Docker Engine is not running in WSL Ubuntu.
    echo [INFO] Attempting to start Docker Engine...
    echo.

    wsl -d Ubuntu -- bash -c "sudo systemctl start docker 2>/dev/null || sudo service docker start 2>/dev/null"

    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to start Docker Engine automatically.
        echo [INFO] Please start Docker Engine manually:
        echo        1. Open WSL: wsl -d Ubuntu
        echo        2. Run: sudo systemctl start docker
        echo        3. Check status: sudo systemctl status docker
        echo        4. Retry this script
        echo.
        pause
        exit /b 1
    )

    echo.
    echo [INFO] Waiting for Docker Engine to become active (max 60 seconds)...
    echo.

    setlocal EnableDelayedExpansion
    set "wait_count=0"
    set "max_wait=30"

    :WAIT_FOR_DOCKER
        if !wait_count! geq !max_wait! (
            echo.
            echo [ERROR] Docker Engine failed to start within timeout period.
            echo [INFO] Please check Docker status:
            echo        wsl -d Ubuntu
            echo        sudo systemctl status docker
            echo        sudo journalctl -u docker.service -n 50
            echo.
            endlocal
            pause
            exit /b 1
        )

    timeout /t 2 /nobreak >nul
    set /a wait_count+=1

    wsl -d Ubuntu -- bash -c "docker info > /dev/null 2>&1"

    if %errorlevel% neq 0 (
        printf "[INFO] Waiting for Docker in WSL... (%d/%d)\r\n" !wait_count! !max_wait!
        goto WAIT_FOR_DOCKER
    )

    endlocal
    echo.
    echo [OK] Docker Engine is now active.
) else (
    echo [OK] Docker Engine is already running.
)

echo.

REM -------------------------------------------
REM Step 3: Validate Required Folders
REM -------------------------------------------
echo [3/5] Checking Required Folders...
echo.

wsl -d Ubuntu -- bash -c "test -d /deployment/EGAT/Airflow/Airflow && echo /deployment/EGAT/Airflow/Airflow: OK || echo /deployment/EGAT/Airflow/Airflow: MISSING"
if %errorlevel% neq 0 (
    echo [ERROR] Required folder /deployment/EGAT/Airflow/Airflow not found.
    pause
    exit /b 1
)

echo.

REM Check if /inspection folder exists (optional)
wsl -d Ubuntu -- bash -c "test -d /inspection && echo /inspection: OK || echo /inspection: NOT FOUND (optional)"
set INSPECTION_EXISTS=1
wsl -d Ubuntu -- bash -c "test -d /inspection" || set INSPECTION_EXISTS=0

echo.

REM -------------------------------------------
REM Step 4: Start Services
REM -------------------------------------------
echo [4/5] Starting Services...
echo.

call :START_SERVICES
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start services.
    echo [INFO] Check the error messages above for details.
    echo.
    pause
    exit /b 1
)

echo.

REM -------------------------------------------
REM Step 5: Health Check and Launch
REM -------------------------------------------
echo [5/5] Performing Health Check...
echo.

echo [INFO] Waiting for services to initialize (10 seconds)...
timeout /t 10 /nobreak >nul

echo.
echo [INFO] Checking service status...
echo.

wsl -d Ubuntu -- bash -c "
docker ps --format 'table {{.Names}}\t{{.Status}}' | head -20
"

echo.
echo Opening application...
start "" "http://localhost:8501/"

echo.
echo ========================================
echo        Startup Complete
echo ========================================
echo.
echo [INFO] Available Services:
echo.
echo        Streamlit App    http://localhost:8501/
echo        Airflow UI       http://localhost:8080/
echo.
echo [INFO] To stop services, run: StopStandalone.bat
echo.
pause
exit /b 0

:START_SERVICES
    REM Start Airflow and inspection services
    wsl -d Ubuntu -- bash -c "
        set -e
        echo '  -> Starting Airflow services...'
        cd /deployment/EGAT/Airflow/Airflow || { echo 'ERROR: Cannot access Airflow directory'; exit 1; }
        docker compose up -d
        echo '  -> Airflow services started.'
        sleep 5
        
        echo '  -> Starting inspection services...'
        if [ -d '/inspection' ]; then
            cd /inspection || { echo 'WARNING: Cannot access /inspection directory'; exit 0; }
            if [ -f './Stop.sh' ]; then
                echo '  -> Stopping existing inspection services...'
                ./Stop.sh 2>/dev/null || true
            fi
            if [ -f './Run.sh' ]; then
                echo '  -> Starting inspection services...'
                ./Run.sh
            else
                echo '  -> WARNING: Run.sh not found, skipping inspection services'
            fi
        else
            echo '  -> INFO: /inspection directory not found, skipping inspection services'
        fi
    "
    exit /b %errorlevel%
