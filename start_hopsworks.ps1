# Start API server and Streamlit in hopsworks environment

# Activate hopsworks environment
conda activate hopsworks-env

# Change to project directory
cd "c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT"

# Start API server in the background
Write-Host "Starting API server in hopsworks-env (with SHAP installed)..." -ForegroundColor Green
Start-Process -FilePath python -ArgumentList "-m uvicorn api_server:app --host 0.0.0.0 --port 8000 --log-level info" -WorkingDirectory "c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT" -NoNewWindow

Start-Sleep -Seconds 8
Write-Host "Starting Streamlit dashboard..." -ForegroundColor Green
Start-Process -FilePath streamlit -ArgumentList "run app.py" -WorkingDirectory "c:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT" -NoNewWindow

Write-Host "`nBoth services started:" -ForegroundColor Green
Write-Host "- API Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host "- API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
