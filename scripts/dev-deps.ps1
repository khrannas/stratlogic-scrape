# Development Dependencies Management Script (PowerShell)
# This script helps manage the infrastructure dependencies (PostgreSQL, Redis, MinIO)
# for local development without running the main application in Docker.

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if dependencies are running
function Check-DepsStatus {
    Write-Status "Checking dependencies status..."
    
    $postgresRunning = docker ps --format "table {{.Names}}" | Select-String "stratlogic-postgres"
    if ($postgresRunning) {
        Write-Success "PostgreSQL is running"
    } else {
        Write-Warning "PostgreSQL is not running"
    }
    
    $redisRunning = docker ps --format "table {{.Names}}" | Select-String "stratlogic-redis"
    if ($redisRunning) {
        Write-Success "Redis is running"
    } else {
        Write-Warning "Redis is not running"
    }
    
    $minioRunning = docker ps --format "table {{.Names}}" | Select-String "stratlogic-minio"
    if ($minioRunning) {
        Write-Success "MinIO is running"
    } else {
        Write-Warning "MinIO is not running"
    }
}

# Function to start dependencies
function Start-Deps {
    Write-Status "Starting infrastructure dependencies..."
    Set-Location $ProjectRoot
    
    # Start dependencies in detached mode
    docker-compose -f docker-compose.deps.yml up -d
    
    Write-Status "Waiting for services to be healthy..."
    Start-Sleep -Seconds 10
    
    # Check if services are healthy
    $healthy = docker-compose -f docker-compose.deps.yml ps | Select-String "healthy"
    if ($healthy) {
        Write-Success "All dependencies are running and healthy!"
        Write-Status "Services available at:"
        Write-Host "  - PostgreSQL: localhost:5432"
        Write-Host "  - Redis: localhost:6379"
        Write-Host "  - MinIO API: localhost:9000"
        Write-Host "  - MinIO Console: http://localhost:9001"
    } else {
        Write-Warning "Some services may still be starting up. Check status with: .\scripts\dev-deps.ps1 status"
    }
}

# Function to stop dependencies
function Stop-Deps {
    Write-Status "Stopping infrastructure dependencies..."
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.deps.yml down
    Write-Success "Dependencies stopped"
}

# Function to restart dependencies
function Restart-Deps {
    Write-Status "Restarting infrastructure dependencies..."
    Stop-Deps
    Start-Deps
}

# Function to reset dependencies (remove volumes)
function Reset-Deps {
    Write-Warning "This will remove all data from PostgreSQL, Redis, and MinIO!"
    $confirmation = Read-Host "Are you sure you want to continue? (y/N)"
    if ($confirmation -eq "y" -or $confirmation -eq "Y") {
        Write-Status "Stopping and removing dependencies with volumes..."
        Set-Location $ProjectRoot
        docker-compose -f docker-compose.deps.yml down -v
        Write-Success "Dependencies and data removed"
        Write-Status "You can start fresh with: .\scripts\dev-deps.ps1 start"
    } else {
        Write-Status "Reset cancelled"
    }
}

# Function to show logs
function Show-Logs {
    Write-Status "Showing dependencies logs..."
    Set-Location $ProjectRoot
    docker-compose -f docker-compose.deps.yml logs -f
}

# Function to show help
function Show-Help {
    Write-Host "Development Dependencies Management Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\scripts\dev-deps.ps1 [COMMAND]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start     Start infrastructure dependencies (PostgreSQL, Redis, MinIO)"
    Write-Host "  stop      Stop infrastructure dependencies"
    Write-Host "  restart   Restart infrastructure dependencies"
    Write-Host "  reset     Stop dependencies and remove all data (volumes)"
    Write-Host "  status    Check status of running dependencies"
    Write-Host "  logs      Show logs from all dependency services"
    Write-Host "  help      Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\scripts\dev-deps.ps1 start    # Start dependencies for local development"
    Write-Host "  .\scripts\dev-deps.ps1 status   # Check if dependencies are running"
    Write-Host "  .\scripts\dev-deps.ps1 stop     # Stop dependencies when done developing"
}

# Main script logic
switch ($Command.ToLower()) {
    "start" {
        Start-Deps
    }
    "stop" {
        Stop-Deps
    }
    "restart" {
        Restart-Deps
    }
    "reset" {
        Reset-Deps
    }
    "status" {
        Check-DepsStatus
    }
    "logs" {
        Show-Logs
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}
