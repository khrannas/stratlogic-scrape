#!/bin/bash

# StratLogic Scraping System - Development Startup Script

set -e

echo "🚀 Starting StratLogic Scraping System..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please update .env file with your configuration before continuing"
    echo "   You can edit the file and run this script again"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it and try again."
    exit 1
fi

echo "🐳 Starting services with Docker Compose..."

# Start services
docker-compose up -d postgres redis minio

echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL
echo "📊 Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U stratlogic_user -d stratlogic > /dev/null 2>&1; do
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Wait for Redis
echo "🔴 Waiting for Redis..."
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Redis is ready"

# Wait for MinIO
echo "📦 Waiting for MinIO..."
until curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    sleep 2
done
echo "✅ MinIO is ready"

echo "🔧 Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install --with-deps chromium

echo "🏗️  Creating database tables..."

# Create database tables
python -c "
from src.core.database import create_tables
from src.core.config import settings
print('Creating database tables...')
create_tables()
print('Database tables created successfully!')
"

echo "🚀 Starting application..."

# Start the application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ StratLogic Scraping System is running!"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo "📊 MinIO Console: http://localhost:9001"
echo ""
echo "Press Ctrl+C to stop the application"
