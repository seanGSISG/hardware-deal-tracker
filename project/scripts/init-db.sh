#!/bin/bash
set -e

echo "Initializing Hardware Deal Tracker database..."

until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

echo "Enabling pgvector extension..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;" || true

echo "Database initialization complete!"
