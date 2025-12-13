# Setup Clean Environment for Bitcoin ML Project
# Run this to create a properly named environment

Write-Host "="*70
Write-Host "BITCOIN ML PROJECT - ENVIRONMENT SETUP"
Write-Host "="*70

Write-Host "`n[1] Creating new environment: bitcoin-ml-env"
conda create -n bitcoin-ml-env python=3.10 -y

Write-Host "`n[2] Activating environment..."
conda activate bitcoin-ml-env

Write-Host "`n[3] Installing core ML packages..."
pip install scikit-learn==1.3.0 pandas numpy matplotlib seaborn

Write-Host "`n[4] Installing deep learning..."
pip install tensorflow prophet

Write-Host "`n[5] Installing explainability..."
pip install lime shap

Write-Host "`n[6] Installing API packages..."
pip install fastapi uvicorn pydantic requests

Write-Host "`n[7] Installing utilities..."
pip install yfinance alpha-vantage python-dotenv joblib

Write-Host "`n"
Write-Host "="*70
Write-Host "SETUP COMPLETE!"
Write-Host "="*70
Write-Host "`nTo use this environment:"
Write-Host "  conda activate bitcoin-ml-env"
Write-Host "`nTo remove old environment (optional):"
Write-Host "  conda deactivate"
Write-Host "  conda remove -n hopsworks-env --all -y"
