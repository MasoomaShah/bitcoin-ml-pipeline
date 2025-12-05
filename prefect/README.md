# Prefect ML Pipeline

Orchestrated ML workflow for World Bank GDP growth prediction with retry logic and notifications.

## Pipeline Overview

The pipeline includes the following stages:

1. **Data Ingestion** - Load World Bank GDP data from CSV
2. **Feature Engineering** - Create rolling features, handle missing values, scale data
3. **Train/Test Split** - Temporal split for time-series data
4. **Model Training** - Train RandomForest regression + classification models
5. **Model Evaluation** - Calculate metrics (RMSE, R², Accuracy, F1)
6. **Model Versioning** - Save models with version tags and update manifest

## Features

- ✅ **Retry Logic**: Automatic retries on task failures (configurable per task)
- ✅ **Error Handling**: Graceful error handling with detailed logging
- ✅ **Notifications**: Success/failure alerts via Discord, Slack, or Email
- ✅ **Concurrent Execution**: Tasks run in parallel where possible
- ✅ **Model Versioning**: Automatic versioning with manifest updates

## Setup

### 1. Install Prefect (if not already installed)

```bash
pip install prefect
```

### 2. Configure Notifications (Optional)

Set environment variables for your preferred notification channel:

**Discord:**
```powershell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
```

**Slack:**
```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**Email (via webhook service like Zapier/Make.com):**
```powershell
$env:EMAIL_WEBHOOK_URL = "https://your-email-webhook-url.com"
```

#### How to get Discord webhook:
1. Open Discord → Server Settings → Integrations → Webhooks
2. Click "New Webhook"
3. Copy the webhook URL

#### How to get Slack webhook:
1. Go to https://api.slack.com/apps
2. Create new app → Incoming Webhooks → Activate
3. Add webhook to workspace and copy URL

### 3. Prepare Data

Ensure your data file exists at:
```
data/raw/world_bank_gdp.csv
```

Required columns: `date`, `GDP`, `Population`, `Inflation`, `Unemployment`

## Running the Pipeline

### Option A: Run Locally (Quick Test)

```powershell
# From project root
python prefect\flows\ml_pipeline.py
```

### Option B: Run via Prefect CLI

```powershell
# Start Prefect server (in separate terminal)
prefect server start

# Run the flow
prefect deployment run ml-training-pipeline
```

### Option C: Run with Custom Parameters

```python
from prefect.flows.ml_pipeline import ml_training_pipeline

result = ml_training_pipeline(
    data_path="data/raw/world_bank_gdp.csv",
    test_years=2,
    output_dir="models",
    notification_type="discord",  # or "slack" or "email"
    reg_hyperparams={'n_estimators': 200, 'max_depth': 15},
    clf_hyperparams={'n_estimators': 200, 'max_depth': 15}
)
```

### Option D: Run via Docker Compose

```powershell
# Start Prefect service (defined in docker-compose.yml)
docker compose --profile prefect up

# In another terminal, register and run the flow
docker exec -it mlproject_prefect prefect deployment build prefect/flows/ml_pipeline.py:ml_training_pipeline -n "ml-pipeline" --apply
docker exec -it mlproject_prefect prefect deployment run ml-training-pipeline/ml-pipeline
```

## Scheduled Runs

### Create a scheduled deployment:

```powershell
# Daily at 2 AM
prefect deployment build prefect\flows\ml_pipeline.py:ml_training_pipeline `
    -n "daily-training" `
    --cron "0 2 * * *" `
    --apply

# Weekly on Sunday
prefect deployment build prefect\flows\ml_pipeline.py:ml_training_pipeline `
    -n "weekly-training" `
    --cron "0 2 * * 0" `
    --apply
```

## Monitoring

### View Pipeline Runs

```powershell
# Start Prefect UI
prefect server start
```

Open browser: http://localhost:4200

### Check Flow Status

```powershell
prefect flow-run ls
```

### View Logs

```powershell
prefect flow-run logs <flow-run-id>
```

## Retry Configuration

Tasks are configured with automatic retries:

- **Data Ingestion**: 3 retries, 10s delay
- **Feature Engineering**: 2 retries, 5s delay
- **Model Training**: 2 retries, 10s delay
- **Model Saving**: 2 retries, 5s delay
- **Notifications**: 2 retries, 5s delay

The entire flow has 1 retry with 30s delay.

## Output

Models are saved to `models/` with the following structure:

```
models/
├── manifest.json                              # Registry manifest
├── vYYYYMMDDTHHMMSSZ_reg_model.pkl           # Regression model
├── vYYYYMMDDTHHMMSSZ_clf_model.pkl           # Classification model
├── vYYYYMMDDTHHMMSSZ_scaler.pkl              # Feature scaler
├── vYYYYMMDDTHHMMSSZ_feature_columns.json    # Feature list
└── vYYYYMMDDTHHMMSSZ_training_metadata.json  # Metrics and metadata
```

## Troubleshooting

### Pipeline fails to import src modules

Ensure you're running from project root:
```powershell
cd "C:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT"
python prefect\flows\ml_pipeline.py
```

### Notifications not sending

Check that webhook URL is set:
```powershell
echo $env:DISCORD_WEBHOOK_URL
```

If empty, set it (see Setup section).

### Models not loading in API

After pipeline completes, reload API models:
```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/reload-models' -Method Post
```

## Example Output

```
============================================================
STEP 1: DATA INGESTION
============================================================
✓ Loaded data: 500 rows, 5 columns
✓ Data validation passed
  Date range: 2000-01-01 to 2024-12-31
  Features: date, GDP, Population, Inflation, Unemployment

============================================================
STEP 2: FEATURE ENGINEERING
============================================================
✓ Feature engineering complete
  Processed shape: (500, 6)
  Feature columns: ['GDP', 'Population', 'Inflation', 'Unemployment', 'GDP_rolling3']
  Scaler fitted: StandardScaler

...

============================================================
  ✅ PIPELINE COMPLETED SUCCESSFULLY
  Duration: 45.23s
============================================================
```

## Next Steps

1. Set up scheduled runs for automated retraining
2. Configure monitoring alerts in Prefect UI
3. Integrate with CI/CD for automated deployments
4. Add more sophisticated hyperparameter tuning
5. Implement A/B testing for model versions
