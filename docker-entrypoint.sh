#!/bin/bash
set -e

# Handle Airflow database upgrade if requested
if [ "$_AIRFLOW_DB_UPGRADE" = "true" ]; then
    echo "Upgrading Airflow database..."
    airflow db upgrade
    echo "Airflow database upgrade completed."
fi

# Handle Airflow user creation if requested
if [ "$_AIRFLOW_WWW_USER_CREATE" = "true" ]; then
    echo "Creating Airflow user..."
    airflow users create \
        --username "${_AIRFLOW_WWW_USER_USERNAME:-airflow}" \
        --firstname "${_AIRFLOW_WWW_USER_FIRSTNAME:-Airflow}" \
        --lastname "${_AIRFLOW_WWW_USER_LASTNAME:-Admin}" \
        --role Admin \
        --email "${_AIRFLOW_WWW_USER_EMAIL:-admin@airflow.local}" \
        --password "${_AIRFLOW_WWW_USER_PASSWORD:-airflow}" \
        2>/dev/null || echo "User creation skipped (user may already exist)"
    echo "Airflow user creation completed."
fi

# Function to run Airflow commands
run_airflow() {
    local command="$1"
    shift
    
    case "$command" in
        webserver|scheduler|flower|triggerer|cli)
            exec airflow "$command" "$@"
            ;;
        worker)
            # In Airflow 2.x, the worker command is 'airflow celery worker'
            exec airflow celery worker "$@"
            ;;
        celery)
            # Handle 'celery worker' style commands
            exec airflow celery "$@"
            ;;
        *)
            echo "Unknown Airflow command: $command"
            exit 1
            ;;
    esac
}

# Check if running as root (Airflow init container or root mode)
if [ "$(id -u)" = "0" ]; then
    # Set proper permissions for Airflow directories
    mkdir -p /opt/airflow/{dags,logs,plugins,configs}
    chown -R airflow:airflow /opt/airflow 2>/dev/null || true
    
    # If running as root with airflow command, switch to airflow user
    if [ "$1" = "webserver" ] || [ "$1" = "scheduler" ] || [ "$1" = "worker" ] || [ "$1" = "flower" ] || [ "$1" = "triggerer" ] || [ "$1" = "cli" ] || [ "$1" = "celery" ]; then
        exec gosu airflow "$0" "$@"
    fi
fi

# Check if command is an Airflow command
if [ "$1" = "webserver" ] || [ "$1" = "scheduler" ] || [ "$1" = "worker" ] || [ "$1" = "flower" ] || [ "$1" = "triggerer" ] || [ "$1" = "cli" ] || [ "$1" = "celery" ]; then
    run_airflow "$@"
elif [ "$1" = "streamlit" ] || [ "$1" = "run" ] || [ -z "$1" ]; then
    # Default: run Streamlit app
    exec streamlit run /app/app_prototype.py --server.port=8501 --server.address=0.0.0.0
else
    # Execute arbitrary command
    exec "$@"
fi
