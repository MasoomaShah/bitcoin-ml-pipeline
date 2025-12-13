#!/bin/bash
# Docker Quick Start Script for Linux/Mac
# Run with: ./docker-start.sh

echo "🐳 Bitcoin ML Pipeline - Docker Startup"
echo "======================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running. Please start Docker."
    exit 1
fi
echo "✓ Docker is running"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file. Edit it if needed."
fi

# Check if models exist
if [ ! -f "models/manifest.json" ]; then
    echo "⚠ No trained models found in models/ directory"
    read -p "Would you like to train models first? (y/n) " train
    if [ "$train" = "y" ]; then
        echo "Training models..."
        python src/train_with_feature_store.py --experiment-models
        echo "✓ Training complete"
    else
        echo "⚠ Warning: Dashboard may not work without trained models"
    fi
fi

echo ""
echo "Select deployment option:"
echo "1. Full Stack (API + Dashboard + Database)"
echo "2. API Only"
echo "3. Dashboard Only"
echo "4. Full Stack + Prefect"
echo "5. Stop All Services"
echo "6. View Logs"
echo ""

read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo "🚀 Starting Full Stack..."
        docker compose up --build
        ;;
    2)
        echo "🚀 Starting API Only..."
        docker compose up --build api
        ;;
    3)
        echo "🚀 Starting Dashboard Only..."
        docker compose up --build dashboard
        ;;
    4)
        echo "🚀 Starting Full Stack + Prefect..."
        docker compose --profile prefect up --build
        ;;
    5)
        echo "🛑 Stopping All Services..."
        docker compose down
        echo "✓ All services stopped"
        ;;
    6)
        echo "📊 Viewing Logs..."
        docker compose logs -f
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
