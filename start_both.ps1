# Start API server and Streamlit dashboard together

$projectPath = Get-Location
Write-Host "Starting API server on port 8000..." -ForegroundColor Green
Start-Process -FilePath python -ArgumentList "-m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $projectPath -NoNewWindow

Start-Sleep -Seconds 5
Write-Host "Starting Streamlit dashboard on port 8501..." -ForegroundColor Green
Start-Process -FilePath streamlit -ArgumentList "run app.py" -WorkingDirectory $projectPath -NoNewWindow

Write-Host "Both services started:" -ForegroundColor Green
Write-Host "- API Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host "- API Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "- API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
