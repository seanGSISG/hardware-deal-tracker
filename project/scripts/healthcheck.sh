#!/bin/bash
set -e

echo "Hardware Deal Tracker - Health Check"
echo "===================================="

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "  OK  $name"
        return 0
    else
        echo "  FAIL $name"
        return 1
    fi
}

check_service "PostgreSQL" "http://localhost:8000/api/v1/health"
check_service "Backend API" "http://localhost:8000/api/v1/health"
check_service "n8n" "http://localhost:5678/healthz"
check_service "Frontend" "http://localhost:3000"

echo ""
echo "Redis check:"
docker compose exec redis redis-cli ping 2>/dev/null && echo "  OK  Redis" || echo "  FAIL Redis"
