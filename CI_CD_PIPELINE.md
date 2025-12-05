# CI/CD Pipeline Documentation

## Overview

This ML project implements a complete **Continuous Integration & Continuous Deployment (CI/CD)** pipeline using GitHub Actions. The pipeline automates code checks, testing, model training, validation, and deployment.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Push Event                        │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐         ┌─────────┐        ┌──────────┐
    │    CI   │         │ ML Tests│        │   CD     │
    │  Tests  │         │ Pipeline│        │ Deployment
    └─────────┘         └─────────┘        └──────────┘
         │                   │                   │
         ├─ Code Quality     ├─ Data Validation ├─ Build Container
         ├─ Unit Tests       ├─ Feature Tests   ├─ Train Model
         ├─ Data Validation  ├─ Model Tests     ├─ Validate Models
         ├─ API Tests        ├─ Regression Tests├─ Security Scan
         │                   ├─ Performance     ├─ Deploy Registry
         │                   │   Benchmarks     │
         │                   ├─ Model Compare   │
         │                   │                  │
         └───────────────────┴──────────────────┘
                             │
                    ▼ All Workflows Pass
                    
            ✅ Ready for Production
```

## Workflows

### 1. **CI Pipeline** (`.github/workflows/ci.yml`)
**Trigger**: `push`, `pull_request` on `main` or `develop`

Runs on every push/PR to catch issues early:

#### Jobs:

**a) Code Quality** (`code-quality`)
- ✅ Black (code formatter check)
- ✅ isort (import sorter check)
- ✅ Flake8 (PEP8 linter)
- ✅ Pylint (code complexity)

**b) Unit Tests** (`unit-tests`)
- ✅ Multi-version testing (Python 3.10, 3.11)
- ✅ Pytest with coverage reporting
- ✅ Coverage upload to Codecov
- ✅ 30-second timeout protection

**c) Data Validation** (`data-validation`)
- ✅ CSV file integrity checks
- ✅ Row/column count verification
- ✅ Missing value detection
- ✅ Data type validation

**d) API Integration Tests** (`api-tests`)
- ✅ FastAPI server startup
- ✅ Endpoint testing
- ✅ API response validation
- ✅ Error log collection

**Duration**: ~3-5 minutes

---

### 2. **ML Tests Pipeline** (`.github/workflows/ml-tests.yml`)
**Trigger**: `push`, `pull_request` on `main` or `develop`

Validates ML-specific components:

#### Jobs:

**a) Data Checks** (`data-checks`)
- ✅ CoinGecko API data fetching (Bitcoin)
- ✅ Data quality validation
- ✅ Date range verification
- ✅ Local data file validation

**b) Feature Engineering** (`feature-tests`)
- ✅ Technical indicator calculation
- ✅ Feature count validation
- ✅ NaN detection
- ✅ Data leakage prevention

**c) Model Tests** (`model-tests`)
- ✅ RandomForest training
- ✅ XGBoost training
- ✅ Model output validation
- ✅ Full pipeline execution

**d) Regression Tests** (`regression-tests`)
- ✅ Test suite execution
- ✅ Multi-threaded test runner
- ✅ Detailed error reporting

**e) Performance Benchmarking** (`performance-benchmark`)
- ✅ Training time measurement
- ✅ Inference throughput
- ✅ Model size verification
- ✅ Performance thresholds

**f) Model Comparison** (`model-comparison`)
- ✅ Cross-validation scoring
- ✅ Model architecture comparison
- ✅ Best model selection

**Duration**: ~5-8 minutes

---

### 3. **CD Pipeline** (`.github/workflows/cd.yml`)
**Trigger**: `push` on `main` branch (after CI passes)

Automates building, training, and deployment:

#### Jobs:

**a) Build Container** (`build-container`)
- ✅ Docker image build with Buildx
- ✅ Multi-platform support
- ✅ Layer caching optimization
- ✅ Push to GitHub Container Registry (ghcr.io)
- ✅ Automated semantic versioning

**b) Train Model** (`train-model`)
- ✅ Run ML pipeline (`test_prefect_pipeline.py`)
- ✅ Generate trained models
- ✅ Upload model artifacts (30-day retention)
- ✅ Upload training logs (7-day retention)
- ✅ Always runs on main branch

**c) Validate Models** (`validate-models`)
- ✅ Download trained models from artifact storage
- ✅ Check manifest integrity
- ✅ Verify model files (.pkl, .json)
- ✅ Performance threshold validation (≥65% accuracy)
- ✅ Generate validation report

**d) Security Scan** (`security-scan`)
- ✅ Trivy vulnerability scanning
- ✅ Filesystem scan
- ✅ SARIF report generation
- ✅ Upload to GitHub Security tab

**e) Deploy** (`deploy`)
- ✅ Download validated models
- ✅ Push to artifact registry
- ✅ Create deployment tags
- ✅ Send deployment notification

**Duration**: ~10-25 minutes (includes training)

---

## Running Workflows

### Manual Trigger
```bash
# Use GitHub CLI
gh workflow run ci.yml
gh workflow run ml-tests.yml
gh workflow run cd.yml

# Or trigger via push
git push origin main
```

### View Status
```bash
# Using GitHub CLI
gh workflow view ci.yml
gh run list

# Or check Actions tab in GitHub
```

### View Logs
```bash
gh run view <run-id> --log
```

---

## Environment Variables & Secrets

### Required Secrets (GitHub Settings → Secrets)

None required for basic operation! However, you can add:

```yaml
DISCORD_WEBHOOK_URL          # For pipeline notifications
SLACK_WEBHOOK_URL            # For Slack notifications
DOCKER_REGISTRY_USERNAME     # For custom registry
DOCKER_REGISTRY_TOKEN        # For custom registry
```

### Available Environments (CI Only)

```yaml
PYTHONIOENCODING=utf-8       # UTF-8 encoding for Python
```

---

## Workflow Configuration

### Adding New Tests

1. **Add unit test file** to `tests/` directory:
```python
# tests/test_my_feature.py
import pytest

def test_feature():
    assert True
```

2. Commit and push - CI automatically discovers and runs it!

### Customizing Test Coverage

Edit `.github/workflows/ci.yml`:
```yaml
- name: Run unit tests with coverage
  run: |
    pytest tests/ -v --cov=src --cov=api --cov-report=xml
```

### Adjusting Performance Thresholds

Edit `.github/workflows/cd.yml`:
```yaml
if accuracy >= 0.65:  # Change threshold here
    print('✓ Model meets threshold')
```

### Adding New Data Sources

Edit `.github/workflows/ml-tests.yml` in `data-checks`:
```yaml
- name: Validate new data source
  run: |
    python -c "
    # Add data validation logic
    "
```

---

## Monitoring & Debugging

### CI/CD Dashboard
- **GitHub**: Repository → Actions tab
- Shows status, runtime, logs for each workflow run

### Key Metrics to Watch

```
┌─ Code Quality
│  ├─ Linting errors
│  └─ Code complexity
│
├─ Test Coverage
│  ├─ Unit test pass rate
│  └─ Coverage percentage (target: >80%)
│
├─ Data Quality
│  ├─ Missing values
│  └─ Data schema validation
│
├─ Model Performance
│  ├─ Accuracy (target: >65%)
│  ├─ F1 Score
│  └─ Training time
│
└─ Security
   ├─ Vulnerabilities found
   └─ Dependency updates
```

### Debugging Failed Workflows

1. **Check logs**: Click failed job → View logs
2. **Common issues**:
   - Missing dependencies: Add to `requirements.txt`
   - Import errors: Check Python paths
   - API timeouts: Increase timeout or retry
   - Memory issues: Check agent resources

3. **Re-run workflow**:
```bash
gh run rerun <run-id>
```

---

## Performance & Resource Usage

### CI Pipeline
- **Runtime**: 3-5 minutes
- **CPU**: 2 cores
- **Memory**: 4GB
- **Disk**: 2GB

### CD Pipeline  
- **Runtime**: 10-25 minutes (including model training)
- **CPU**: 2 cores
- **Memory**: 8GB
- **Disk**: 5GB

### Cost (GitHub Actions)
- ✅ **Free for public repos** (unlimited minutes)
- ⚠️ **Free for private repos**: 2,000 minutes/month
- 💳 After limit: $0.24/minute

---

## Best Practices

### 1. Branch Strategy
```
main (production)
  ↑ merged from
develop (staging)
  ↑ merged from
feature/* (development)
```

### 2. Commit Messages
```
Format: <type>(<scope>): <subject>

Examples:
feat(model): improve XGBoost hyperparameters
fix(api): handle null responses
docs(ci): update pipeline docs
test(data): add bitcoin validation tests
```

### 3. PR Requirements
- ✅ All CI checks passing
- ✅ Code coverage >80%
- ✅ At least 1 review approval
- ✅ No security vulnerabilities

### 4. Deployment Readiness
Ensure before merging to main:
- [ ] All tests passing locally
- [ ] No breaking changes
- [ ] Updated documentation
- [ ] Model performance meets threshold

---

## Troubleshooting

### "Workflow not triggering"
- Check branch name matches trigger condition
- Verify `.github/workflows/` files are committed
- Ensure file has valid YAML syntax

### "Tests timing out"
- Increase timeout: `--timeout=60` in pytest
- Reduce data size for testing
- Check for infinite loops

### "Model accuracy low"
- Check data quality in logs
- Verify feature engineering runs
- Review training parameters

### "Docker build fails"
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Review disk space in runner

### "Permission denied"
- Add GITHUB_TOKEN permissions in workflow
- Check file access in Docker
- Verify artifact paths

---

## Extending the Pipeline

### Add Email Notifications
```yaml
- name: Send email notification
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USER }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Pipeline completed
    to: your-email@gmail.com
    from: ci@pipeline.local
```

### Add Slack Notifications
```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Pipeline ${{ job.status }}: ${{ github.repository }}"
      }
```

### Add Performance Tracking
```yaml
- name: Track performance metrics
  uses: actions/upload-artifact@v4
  with:
    name: performance-metrics
    path: metrics.json
```

---

## Deployment Strategy

### Development (Every Commit)
```yaml
on:
  push:
    branches: [develop]
# Deploys to dev environment
```

### Staging (Every Push to main)
```yaml
on:
  push:
    branches: [main]
  workflow_run:
    workflows: ["CI - Code Checks"]
    types: [completed]
# Deploys after all tests pass
```

### Production (Manual)
```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deploy to:'
        required: true
        default: 'staging'
```

---

## Monitoring & Alerts

### GitHub Status Checks
- **Required** for merge to main
- Shows real-time CI/CD status
- Blocks PR if checks fail

### Artifact Retention
- **Models**: 30 days
- **Logs**: 7 days
- **Coverage reports**: 30 days

### Auto-cleanup
Workflows automatically:
- Delete old artifacts after retention expires
- Clean up temporary files
- Remove failed job logs after 90 days

---

## Next Steps

1. **Push to GitHub** to trigger first CI/CD run
2. **Monitor Actions tab** for results
3. **Check logs** for any issues
4. **Set up Discord/Slack** for notifications (optional)
5. **Add branch protection** requiring CI to pass

---

## Summary Table

| Workflow | Trigger | Duration | Purpose |
|----------|---------|----------|---------|
| **CI** | push/PR | 3-5 min | Code checks, unit tests, data validation |
| **ML Tests** | push/PR | 5-8 min | Data quality, feature tests, model validation |
| **CD** | push main | 10-25 min | Build, train, validate, deploy |

---

**Status**: ✅ **FULLY IMPLEMENTED & READY**

All CI/CD workflows are configured and ready for production use!
