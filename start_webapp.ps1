# Bitcoin ML Web App Launcher
# Run this script to start both the Streamlit dashboard and FastAPI server

Write-Host "🚀 Starting Bitcoin ML Web App..." -ForegroundColor Cyan
Write-Host ""

# Check if models exist
if (-not (Test-Path "models/manifest.json")) {
    Write-Host "⚠️  No trained models found!" -ForegroundColor Yellow
    Write-Host "   Please train models first:" -ForegroundColor Yellow
    Write-Host "   python src/train_with_feature_store.py" -ForegroundColor White
    Write-Host ""
    $train = Read-Host "Would you like to train models now? (y/n)"
    if ($train -eq "y") {
        python src/train_with_feature_store.py
        Write-Host ""
    } else {
        exit
    }
}

Write-Host "✓ Models found" -ForegroundColor Green
Write-Host ""

# Ask which component to run
Write-Host "Select what to run:" -ForegroundColor Cyan
Write-Host "1. Streamlit Dashboard only (recommended)" -ForegroundColor White
Write-Host "2. FastAPI Server only" -ForegroundColor White
Write-Host "3. Both Dashboard and API Server" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1/2/3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🎨 Starting Streamlit Dashboard..." -ForegroundColor Green
        Write-Host "   Opening at http://localhost:8501" -ForegroundColor White
        Write-Host ""
        streamlit run app.py
    }
    "2" {
        Write-Host ""
        Write-Host "⚡ Starting FastAPI Server..." -ForegroundColor Green
        Write-Host "   API: http://localhost:8000" -ForegroundColor White
        Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor White
        Write-Host ""
        python api_server.py
    }
    "3" {
        Write-Host ""
        Write-Host "🚀 Starting both components..." -ForegroundColor Green
        Write-Host ""
        Write-Host "   Dashboard: http://localhost:8501" -ForegroundColor White
        Write-Host "   API: http://localhost:8000" -ForegroundColor White
        Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
        Write-Host ""
        
        # Start API server in background
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "python api_server.py"
        
        # Wait a bit for API to start
        Start-Sleep -Seconds 2
        
        # Start Streamlit dashboard
        streamlit run app.py
    }
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
    }
}
