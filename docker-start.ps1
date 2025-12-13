# Docker Quick Start Script for Windows
# Run with: .\docker-start.ps1

Write-Host "🐳 Bitcoin ML Pipeline - Docker Startup" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "⚠ .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file. Edit it if needed." -ForegroundColor Green
}

# Check if models exist
if (-not (Test-Path "models/manifest.json")) {
    Write-Host "⚠ No trained models found in models/ directory" -ForegroundColor Yellow
    $train = Read-Host "Would you like to train models first? (y/n)"
    if ($train -eq "y") {
        Write-Host "Training models..." -ForegroundColor Yellow
        python src/train_with_feature_store.py --experiment-models
        Write-Host "✓ Training complete" -ForegroundColor Green
    } else {
        Write-Host "⚠ Warning: Dashboard may not work without trained models" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Select deployment option:" -ForegroundColor Cyan
Write-Host "1. Full Stack (API + Dashboard + Database)"
Write-Host "2. API Only"
Write-Host "3. Dashboard Only"
Write-Host "4. Full Stack + Prefect"
Write-Host "5. Stop All Services"
Write-Host "6. View Logs"
Write-Host ""

$choice = Read-Host "Enter choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "🚀 Starting Full Stack..." -ForegroundColor Green
        docker compose up --build
    }
    "2" {
        Write-Host "🚀 Starting API Only..." -ForegroundColor Green
        docker compose up --build api
    }
    "3" {
        Write-Host "🚀 Starting Dashboard Only..." -ForegroundColor Green
        docker compose up --build dashboard
    }
    "4" {
        Write-Host "🚀 Starting Full Stack + Prefect..." -ForegroundColor Green
        docker compose --profile prefect up --build
    }
    "5" {
        Write-Host "🛑 Stopping All Services..." -ForegroundColor Yellow
        docker compose down
        Write-Host "✓ All services stopped" -ForegroundColor Green
    }
    "6" {
        Write-Host "📊 Viewing Logs..." -ForegroundColor Cyan
        docker compose logs -f
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
        exit 1
    }
}
