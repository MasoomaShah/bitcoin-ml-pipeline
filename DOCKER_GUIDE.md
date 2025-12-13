# Docker Deployment Guide

## 🐳 Full Stack Docker Setup

This guide covers deploying the complete Bitcoin ML pipeline using Docker.

## 📋 Prerequisites

- Docker Desktop installed (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- At least 4GB RAM available for containers
- Trained models in `models/` directory

## 🏗️ Architecture

The full stack consists of:

1. **FastAPI Backend** (`api`) - Port 8000
   - REST API for predictions
   - Model serving
   - Health checks

2. **Streamlit Dashboard** (`dashboard`) - Port 8501
   - Interactive web UI
   - Real-time predictions
   - Price charts and analytics

3. **PostgreSQL Database** (`db`) - Port 5432
   - Optional: For storing predictions/metrics
   - Persistent data storage

4. **Prefect Server** (`prefect`) - Port 4200 [Optional]
   - Workflow orchestration
   - Scheduled training

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys (optional, has defaults)
nano .env
```

### 2. Build and Start All Services

```bash
# Start API + Dashboard + Database
docker compose up --build

# Or run in background (detached mode)
docker compose up -d --build
```

### 3. Access the Applications

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health
- **Database**: localhost:5432

### 4. Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

## 🎯 Individual Service Commands

### Start Only Specific Services

```bash
# Only API
docker compose up api

# Only Dashboard
docker compose up dashboard

# API + Dashboard (no DB)
docker compose up api dashboard
```

### Start with Prefect

```bash
# Include Prefect workflow orchestration
docker compose --profile prefect up --build
```

## 🔧 Development Mode

### Live Code Reloading

The containers are configured with volume mounts for development:

```yaml
volumes:
  - ./models:/app/models:ro    # Read-only models
  - ./data:/app/data:rw         # Read-write data
```

For live code changes, rebuild specific services:

```bash
# Rebuild and restart dashboard
docker compose up -d --build dashboard

# Rebuild and restart API
docker compose up -d --build api
```

## 📊 View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f dashboard
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 dashboard
```

## 🔍 Health Checks

All services have health checks configured:

```bash
# Check service status
docker compose ps

# Manual health check
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

## 🗄️ Database Management

### Connect to PostgreSQL

```bash
# Using Docker exec
docker exec -it bitcoin_ml_db psql -U postgres -d bitcoin_ml

# Using external client
psql -h localhost -p 5432 -U postgres -d bitcoin_ml
```

### Backup Database

```bash
docker exec bitcoin_ml_db pg_dump -U postgres bitcoin_ml > backup.sql
```

### Restore Database

```bash
docker exec -i bitcoin_ml_db psql -U postgres bitcoin_ml < backup.sql
```

## 🔐 Environment Variables

Create a `.env` file with:

```env
# Required
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=bitcoin_ml

# Optional
MODEL_RELOAD_TOKEN=your_secret_token
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs api
docker compose logs dashboard

# Restart specific service
docker compose restart api
```

### Port Already in Use

```bash
# Change ports in docker-compose.yml
ports:
  - '8001:8000'  # Change external port
```

### Out of Memory

```bash
# Increase Docker memory in Docker Desktop settings
# Or add memory limits in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

### Models Not Found

```bash
# Ensure models exist locally
ls -la models/

# Copy models into running container
docker cp models/. bitcoin_ml_api:/app/models/
docker compose restart api dashboard
```

## 📦 Production Deployment

### Security Checklist

- [ ] Change default PostgreSQL password
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Use Docker secrets for sensitive data
- [ ] Enable container resource limits
- [ ] Set up log aggregation

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Scaling

```bash
# Run multiple API instances
docker compose up --scale api=3

# Behind a load balancer (add nginx service)
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
- name: Build and Push Docker Images
  run: |
    docker compose build
    docker tag bitcoin-ml-api:latest ghcr.io/username/bitcoin-ml-api:latest
    docker push ghcr.io/username/bitcoin-ml-api:latest
```

## 📚 Additional Commands

```bash
# Remove all stopped containers
docker compose rm

# Rebuild without cache
docker compose build --no-cache

# Pull latest base images
docker compose pull

# View resource usage
docker stats

# Execute command in running container
docker compose exec api python -c "print('Hello')"

# Open shell in container
docker compose exec api bash
docker compose exec dashboard bash
```

## 🌐 Network Configuration

Services communicate via the `ml-network` bridge network:

- `api` accessible at `http://api:8000` from other containers
- `dashboard` can call API internally via `http://api:8000`
- `db` accessible at `postgresql://postgres:password@db:5432/bitcoin_ml`

## 🎨 Customization

### Change Ports

Edit `docker-compose.yml`:

```yaml
ports:
  - '8080:8000'  # API on port 8080
  - '8502:8501'  # Dashboard on port 8502
```

### Add Services

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - '6379:6379'
    networks:
      - ml-network
```

## 📖 References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Streamlit Docker Guide](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)

## 🆘 Support

If you encounter issues:

1. Check logs: `docker compose logs -f`
2. Verify health: `docker compose ps`
3. Restart services: `docker compose restart`
4. Clean rebuild: `docker compose down -v && docker compose up --build`
