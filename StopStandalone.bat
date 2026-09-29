@echo off
title Standalone Services Stopper
color 07

echo =====================================================
echo        Stopping Standalone and Airflow Services
echo =====================================================
echo.

echo [INFO] Stopping all services...
echo.

wsl -d Ubuntu -- bash -c "
    echo '  -> Stopping Airflow services...'
    cd /deployment/EGAT/Airflow/Airflow 2>/dev/null && docker compose down 2>/dev/null || echo '  -> Airflow: Not running or folder not found'
    
    echo '  -> Stopping MLFlow services...'
    cd /deployment/EGAT/Airflow/MLFlow 2>/dev/null && docker compose down 2>/dev/null || echo '  -> MLFlow: Not running or folder not found'
    
    echo '  -> Stopping SFTPGo services...'
    cd /deployment/EGAT/Airflow/SFTPGo 2>/dev/null && docker compose down 2>/dev/null || echo '  -> SFTPGo: Not running or folder not found'
    
    echo '  -> Stopping BDM Trigger services...'
    cd /deployment/EGAT/EGAT_BDM_Trigger 2>/dev/null && docker compose down 2>/dev/null || echo '  -> BDM Trigger: Not running or folder not found'
    
    echo '  -> Stopping UpdateModel services...'
    cd /deployment/EGAT/UpdateModel 2>/dev/null && docker compose down 2>/dev/null || echo '  -> UpdateModel: Not running or folder not found'
    
    echo '  -> Stopping inspection services...'
    if [ -d '/inspection' ]; then
        cd /inspection 2>/dev/null && ./Stop.sh 2>/dev/null || echo '  -> Inspection: Not running or Stop.sh not found'
    fi
    
    echo ''
    echo 'All services stopped.'
"

echo.
echo ========================================
echo        Stop Complete
echo ========================================
echo.
pause
