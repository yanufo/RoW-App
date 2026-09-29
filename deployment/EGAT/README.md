# EGAT Airflow Deployment

This directory contains the Docker Compose configuration for deploying the Row Inspection application in the EGAT environment with Airflow integration.

## Prerequisites

1. **Docker and Docker Compose** installed
2. **External Airflow Network**: An existing Docker network named `egat-airflow-network` that connects to:
   - Airflow services (for workflow orchestration)
   - Shared MySQL database (or use the included mysql-shared service)
3. **Build context**: Ensure you're running the command from this directory

## Configuration

### Environment Variables

Copy the example `.env` file and customize for your environment:

```bash
cp .env.example .env
```

Key configuration options:
- `AIRFLOW_URL`: URL to your Airflow webserver (default: `http://host.docker.internal:8080`)
- `AIRFLOW_API_USER`: Airflow API username
- `AIRFLOW_API_PASSWORD`: Airflow API password
- `DB_HOST`: MySQL database host
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name

### Network Setup

The deployment uses an external Docker network (`egat-airflow-network`). If you don't have this network yet, create it:

```bash
docker network create egat-airflow-network
```

## Deployment

### Build and Start

```bash
# From the deployment/EGAT directory
docker compose up -d --build
```

### Check Status

```bash
docker compose ps
```

### View Logs

```bash
# Streamlit app logs
docker compose logs -f row-streamlit-app

# MySQL logs
docker compose logs -f mysql-shared
```

### Stop Services

```bash
docker compose down
```

To also remove volumes (WARNING: this will delete MySQL data):

```bash
docker compose down -v
```

## Application Structure

### Services

1. **row-streamlit-app**: Streamlit application with compiled Python modules
   - Port: 8501
   - Connects to Airflow API for workflow management
   - Connects to MySQL for data persistence

2. **mysql-shared**: MySQL 8.0 database service
   - Persists data in Docker volume
   - Initializes with default credentials from `.env`

### Dockerfile Features

The main Dockerfile (in root directory) includes:

- **Multi-stage build**: Optimized for smaller image size
- **Nuitka compilation**: Critical Python modules are compiled for performance
- **Streamlit optimization**: Pre-built with all dependencies
- **Health checks**: Automatic health monitoring

### Volume Mounts

The container mounts the following paths:

- `/host_home`: Host home directory
- `/data`: General data storage
- `/inspection`: Inspection configuration and results
- `/app/models`: 3D model files for drone inspection

## Troubleshooting

### Connection Issues

If the Streamlit app can't connect to Airflow:
1. Verify Airflow is running and accessible at the configured URL
2. Check that `host.docker.internal` is correctly resolved
3. Ensure the network `egat-airflow-network` exists

### MySQL Connection Issues

1. Verify MySQL is running: `docker compose ps`
2. Check MySQL logs: `docker compose logs mysql-shared`
3. Ensure database credentials match in `.env`

### Build Issues

If you encounter build errors:
1. Ensure git is accessible to clone the repository
2. Check network connectivity
3. Try rebuilding from scratch: `docker compose build --no-cache`

## Environment-Specific Adjustments

### For Production EGAT Environment

1. Update `AIRFLOW_URL` to point to the production Airflow server
2. Use secure database credentials
3. Configure proper volume paths for persistent storage
4. Set up logging aggregation
5. Consider adding authentication for the Streamlit app

## Support

For issues specific to this deployment configuration, contact the development team or check the main application documentation.