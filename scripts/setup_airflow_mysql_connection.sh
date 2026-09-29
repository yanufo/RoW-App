#!/bin/bash
# Setup MySQL connection in Airflow for accessing row_database
# This script should be run after Airflow containers are started

echo "=========================================="
echo "Setting up MySQL connection in Airflow..."
echo "=========================================="

# Connection settings
MYSQL_HOST="host.docker.internal"
MYSQL_PORT="3306"
MYSQL_USER="streamlit_user"
MYSQL_PASSWORD="gve"
MYSQL_NAME="row_database"

# Wait for Airflow webserver to be ready
echo "Waiting for Airflow webserver to be ready..."
for i in {1..30}; do
    if docker exec airflow-airflow-webserver-1 curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "Airflow webserver is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Warning: Airflow webserver not responding, will try to add connection anyway..."
    fi
    sleep 2
done

# Add MySQL connection (using --user airflow since airflow module is installed for airflow user)
echo "Adding MySQL connection 'mysql_row_inspection' to Airflow..."
docker exec --user airflow airflow-airflow-webserver-1 airflow connections add 'mysql_row_inspection' \
    --conn-type 'mysql' \
    --conn-host "$MYSQL_HOST" \
    --conn-port "$MYSQL_PORT" \
    --conn-login "$MYSQL_USER" \
    --conn-password "$MYSQL_PASSWORD" \
    --conn-schema "$MYSQL_NAME" 2>/dev/null

# Verify connection was added
echo ""
echo "Verifying MySQL connection in Airflow..."
docker exec --user airflow airflow-airflow-webserver-1 airflow connections list 2>/dev/null | grep mysql_row_inspection

echo ""
echo "=========================================="
echo "MySQL connection setup complete!"
echo "You can now use 'mysql_row_inspection' in your DAGs"
echo "=========================================="
