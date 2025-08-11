#!/bin/bash

# Development Dependencies Management Script
# This script helps manage the infrastructure dependencies (PostgreSQL, Redis, MinIO)
# for local development without running the main application in Docker.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if dependencies are running
check_deps_status() {
    print_status "Checking dependencies status..."
    
    if docker ps --format "table {{.Names}}" | grep -q "stratlogic-postgres"; then
        print_success "PostgreSQL is running"
    else
        print_warning "PostgreSQL is not running"
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "stratlogic-redis"; then
        print_success "Redis is running"
    else
        print_warning "Redis is not running"
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "stratlogic-minio"; then
        print_success "MinIO is running"
    else
        print_warning "MinIO is not running"
    fi
}

# Function to start dependencies
start_deps() {
    print_status "Starting infrastructure dependencies..."
    cd "$PROJECT_ROOT"
    
    # Start dependencies in detached mode
    docker-compose -f docker-compose.deps.yml up -d
    
    print_status "Waiting for services to be healthy..."
    sleep 10
    
    # Check if services are healthy
    if docker-compose -f docker-compose.deps.yml ps | grep -q "healthy"; then
        print_success "All dependencies are running and healthy!"
        print_status "Services available at:"
        echo "  - PostgreSQL: localhost:5432"
        echo "  - Redis: localhost:6379"
        echo "  - MinIO API: localhost:9000"
        echo "  - MinIO Console: http://localhost:9001"
    else
        print_warning "Some services may still be starting up. Check status with: ./scripts/dev-deps.sh status"
    fi
}

# Function to stop dependencies
stop_deps() {
    print_status "Stopping infrastructure dependencies..."
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.deps.yml down
    print_success "Dependencies stopped"
}

# Function to restart dependencies
restart_deps() {
    print_status "Restarting infrastructure dependencies..."
    stop_deps
    start_deps
}

# Function to reset dependencies (remove volumes)
reset_deps() {
    print_warning "This will remove all data from PostgreSQL, Redis, and MinIO!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping and removing dependencies with volumes..."
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.deps.yml down -v
        print_success "Dependencies and data removed"
        print_status "You can start fresh with: ./scripts/dev-deps.sh start"
    else
        print_status "Reset cancelled"
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing dependencies logs..."
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.deps.yml logs -f
}

# Function to show help
show_help() {
    echo "Development Dependencies Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start infrastructure dependencies (PostgreSQL, Redis, MinIO)"
    echo "  stop      Stop infrastructure dependencies"
    echo "  restart   Restart infrastructure dependencies"
    echo "  reset     Stop dependencies and remove all data (volumes)"
    echo "  status    Check status of running dependencies"
    echo "  logs      Show logs from all dependency services"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start dependencies for local development"
    echo "  $0 status   # Check if dependencies are running"
    echo "  $0 stop     # Stop dependencies when done developing"
}

# Main script logic
case "${1:-help}" in
    start)
        start_deps
        ;;
    stop)
        stop_deps
        ;;
    restart)
        restart_deps
        ;;
    reset)
        reset_deps
        ;;
    status)
        check_deps_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
