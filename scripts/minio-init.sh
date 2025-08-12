#!/bin/bash
# MinIO initialization script for StratLogic Scraper
# This script runs when the MinIO container starts for the first time

set -e

echo "Initializing MinIO for StratLogic Scraper..."

# Wait for MinIO to be ready
until mc alias set myminio http://localhost:9000 minioadmin minioadmin; do
    echo "Waiting for MinIO to be ready..."
    sleep 2
done

# Create buckets
echo "Creating buckets..."
mc mb myminio/stratlogic-artifacts --ignore-existing
mc mb myminio/stratlogic-documents --ignore-existing
mc mb myminio/stratlogic-cache --ignore-existing
mc mb myminio/stratlogic-backups --ignore-existing

# Set bucket policies
echo "Setting bucket policies..."
mc policy set download myminio/stratlogic-artifacts
mc policy set download myminio/stratlogic-documents
mc policy set download myminio/stratlogic-cache
mc policy set download myminio/stratlogic-backups

# Create lifecycle policies for cache cleanup
echo "Setting lifecycle policies..."
mc ilm add myminio/stratlogic-cache --expiry-days 30

echo "MinIO initialization completed successfully!"
