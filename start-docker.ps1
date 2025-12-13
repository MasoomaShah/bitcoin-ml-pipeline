# Start Docker Desktop and Wait for it to be Ready
Write-Host "🐳 Starting Docker Desktop..." -ForegroundColor Cyan

# Check if Docker Desktop is installed
$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (-not (Test-Path $dockerPath)) {
    Write-Host "❌ Docker Desktop not found at: $dockerPath" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is already running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is already running!" -ForegroundColor Green
} catch {
    Write-Host "⏳ Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process $dockerPath
    
    # Wait for Docker to be ready (max 60 seconds)
    $timeout = 60
    $elapsed = 0
    
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 3
        $elapsed += 3
        
        try {
            docker info | Out-Null
            Write-Host "✅ Docker is ready!" -ForegroundColor Green
            break
        } catch {
            Write-Host "⏳ Waiting for Docker... ($elapsed seconds)" -ForegroundColor Yellow
        }
    }
    
    if ($elapsed -ge $timeout) {
        Write-Host "❌ Docker failed to start within $timeout seconds" -ForegroundColor Red
        Write-Host "Please check Docker Desktop manually" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "🚀 Docker is ready! You can now run:" -ForegroundColor Green
Write-Host "   docker compose up --build" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use the quick start script:" -ForegroundColor Green
Write-Host "   .\docker-start.ps1" -ForegroundColor Cyan
