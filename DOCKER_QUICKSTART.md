# 🐳 Docker Full Stack - Quick Reference

## Quick Start

```bash
# Windows
.\docker-start.ps1

# Linux/Mac
chmod +x docker-start.sh
./docker-start.sh
```

## One-Line Commands

```bash
# Start full stack
docker compose up --build

# Start in background
docker compose up -d --build

# Stop all services
docker compose down

# View logs
docker compose logs -f
```

## Access Points

- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

## Files Created

1. **Dockerfile.api** - FastAPI backend container
2. **Dockerfile.streamlit** - Streamlit dashboard container
3. **docker-compose.yml** - Full orchestration (updated)
4. **.env.example** - Environment template
5. **DOCKER_GUIDE.md** - Complete documentation
6. **docker-start.ps1** - Windows quick start
7. **docker-start.sh** - Linux/Mac quick start

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Network (ml-network)      │
│                                          │
│  ┌──────────────┐    ┌───────────────┐  │
│  │  Dashboard   │────│      API      │  │
│  │  (Streamlit) │    │   (FastAPI)   │  │
│  │  Port 8501   │    │   Port 8000   │  │
│  └──────────────┘    └───────┬───────┘  │
│                              │          │
│                    ┌─────────┴────────┐ │
│                    │    PostgreSQL    │ │
│                    │    Port 5432     │ │
│                    └──────────────────┘ │
└─────────────────────────────────────────┘
```

## Status

✅ **COMPLETE** - Full stack Docker setup ready for deployment!
