#!/bin/bash

# EGAT Deployment Validation Script
# Checks if the environment is ready for deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASS++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAIL++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARN++))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo "=========================================="
echo "  EGAT Deployment Validation"
echo "=========================================="
echo ""

# Check Docker
log_info "Checking Docker installation..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | cut -d' ' -f3)
    log_pass "Docker $docker_version installed"
else
    log_fail "Docker is not installed"
fi

# Check Docker Compose
log_info "Checking Docker Compose installation..."
if docker compose version &> /dev/null; then
    compose_version=$(docker compose version 2>&1 | grep -oP '\d+\.\d+\.\d+' | head -1)
    log_pass "Docker Compose $compose_version installed"
else
    log_fail "Docker Compose is not installed"
fi

# Check if running from correct directory
log_info "Checking directory structure..."
if [ -f "Airflowdocker-compose.yml" ]; then
    log_pass "docker-compose.yml found"
else
    log_fail "Airflowdocker-compose.yml not found"
fi

if [ -f "deploy.sh" ]; then
    log_pass "deploy.sh found"
else
    log_warn "deploy.sh not found"
fi

# Check Docker daemon
log_info "Checking Docker daemon..."
if docker info &> /dev/null; then
    log_pass "Docker daemon is running"
else
    log_fail "Docker daemon is not running"
fi

# Check external network
log_info "Checking external network..."
if docker network ls --filter name=egat-airflow-network --format '{{.Name}}' | grep -q "^egat-airflow-network$"; then
    log_pass "Network 'egat-airflow-network' exists"
else
    log_warn "Network 'egat-airflow-network' does not exist. Create it with: docker network create egat-airflow-network"
fi

# Check Dockerfile
log_info "Checking Dockerfile..."
if [ -f "../../Dockerfile" ]; then
    log_pass "Dockerfile found in parent directory"
else
    log_fail "Dockerfile not found in parent directory"
fi

# Check required files in build context
log_info "Checking build context files..."
if [ -f "../../requirements.txt" ]; then
    log_pass "requirements.txt found"
else
    log_warn "requirements.txt not found"
fi

# Check .env file
log_info "Checking environment configuration..."
if [ -f ".env" ]; then
    log_pass ".env file exists"
    
    # Check required environment variables
    if grep -q "AIRFLOW_URL" .env; then
        log_pass "AIRFLOW_URL configured"
    else
        log_warn "AIRFLOW_URL not configured in .env"
    fi
    
    if grep -q "DB_HOST" .env; then
        log_pass "DB_HOST configured"
    else
        log_warn "DB_HOST not configured in .env"
    fi
else
    log_warn ".env file not found. Copy .env.example to .env and configure it."
fi

# Check Airflow accessibility (if URL is configured)
log_info "Checking Airflow accessibility..."
if [ -f ".env" ]; then
    AIRFLOW_URL=$(grep "AIRFLOW_URL" .env | cut -d'=' -f2 | tr -d ' ')
    if [ -n "$AIRFLOW_URL" ]; then
        if curl --output /dev/null --silent --fail "$AIRFLOW_URL"; then
            log_pass "Airflow is accessible at $AIRFLOW_URL"
        else
            log_warn "Cannot reach Airflow at $AIRFLOW_URL. Make sure Airflow is running."
        fi
    fi
fi

# Summary
echo ""
echo "=========================================="
echo "  Validation Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo -e "${YELLOW}Warnings: $WARN${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Environment is ready for deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review and update .env file with your configuration"
    echo "  2. Run: ./deploy.sh up"
    exit 0
else
    echo -e "${RED}✗ Please fix the failed checks before deploying.${NC}"
    exit 1
fi