#!/bin/bash

# EGAT Airflow Deployment Script
# Usage: ./deploy.sh [up|down|logs|status|rebuild]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="Airflowdocker-compose.yml"
PROJECT_NAME="egat-row"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if running from correct directory
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Please run this script from the deployment/EGAT directory."
        exit 1
    fi
    
    log_info "Prerequisites check passed."
}

check_network() {
    log_info "Checking network configuration..."
    
    if ! docker network ls --filter name=egat-airflow-network --format '{{.Name}}' | grep -q "^egat-airflow-network$"; then
        log_warn "Network 'egat-airflow-network' does not exist."
        read -p "Create the network now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker network create egat-airflow-network
            log_info "Network 'egat-airflow-network' created successfully."
        else
            log_warn "Please create the network manually: docker network create egat-airflow-network"
        fi
    else
        log_info "Network 'egat-airflow-network' exists."
    fi
}

check_env_file() {
    if [ ! -f ".env" ]; then
        log_warn ".env file not found."
        read -p "Create .env file from template? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env 2>/dev/null || true
            log_info "Please edit .env file with your configuration."
        fi
    fi
}

cmd_up() {
    log_info "Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d --build
    log_info "Services started. Checking status..."
    sleep 5
    cmd_status
}

cmd_down() {
    log_info "Stopping services..."
    docker compose -f "$COMPOSE_FILE" down
    log_info "Services stopped."
}

cmd_logs() {
    log_info "Showing logs (press Ctrl+C to exit)..."
    docker compose -f "$COMPOSE_FILE" logs -f
}

cmd_status() {
    log_info "Service status:"
    docker compose -f "$COMPOSE_FILE" ps
}

cmd_rebuild() {
    log_info "Rebuilding services..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    log_info "Rebuild complete. Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d
    log_info "Services started."
}

cmd_help() {
    echo "EGAT Airflow Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  up        - Start all services"
    echo "  down      - Stop all services"
    echo "  logs      - View service logs"
    echo "  status    - Show service status"
    echo "  rebuild   - Rebuild and restart services"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 up       # Start services"
    echo "  $0 logs     # View logs"
    echo "  $0 status   # Check status"
}

# Main
case "${1:-help}" in
    up)
        check_prerequisites
        check_network
        check_env_file
        cmd_up
        ;;
    down)
        check_prerequisites
        cmd_down
        ;;
    logs)
        check_prerequisites
        cmd_logs
        ;;
    status)
        check_prerequisites
        cmd_status
        ;;
    rebuild)
        check_prerequisites
        check_network
        check_env_file
        cmd_rebuild
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        log_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac

exit 0