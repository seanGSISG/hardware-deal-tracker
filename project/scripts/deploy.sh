#!/bin/bash
set -e

echo "Hardware Deal Tracker - Deployment"
echo "=================================="

if [ ! -f .env ]; then
    echo "WARNING: .env not found. Using defaults."
fi

echo "Building images..."
docker compose build

echo "Starting infrastructure..."
docker compose up -d postgres redis

echo "Waiting for PostgreSQL..."
sleep 5

echo "Starting backend..."
docker compose up -d backend

echo "Starting remaining services..."
docker compose up -d

echo ""
echo "Deployment complete!"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000/api/v1/docs"
echo "  n8n:       http://localhost:5678"
