# 📊 Data Drift Monitoring Guide

## Overview

Data drift monitoring detects statistical changes in data distribution over time. This is critical for maintaining ML model performance in production.

## Why Data Drift Monitoring Matters

### Real-World Impact
- **Model Performance Degradation**: When data distribution changes, model accuracy drops
- **Business Decisions**: Drift-based alerts enable proactive interventions
- **Compliance**: Documentation of data quality for regulatory requirements
- **Cost Savings**: Early detection prevents massive prediction errors

### Bitcoin Price Prediction Context
Bitcoin price prediction relies on specific technical indicator relationships. When market conditions change:
- Trading volumes may spike or drop
- RSI ranges may shift (oversold/overbought thresholds change)
- MACD behavior patterns may alter
- Price momentum dynamics may reverse

---

## Drift Detection Methods

### 1. Kolmogorov-Smirnov (KS) Test
**What it does**: Tests if two distributions are statistically different  
**Best for**: Continuous variables (price, volume, indicators)  
**Interpretation**:
- **p-value > 0.05**: No significant drift detected
- **p-value ≤ 0.05**: Drift detected (distributions differ)

**Example**:
```python
ks_stat, p_value = engine.ks_test(current_data, 'btc_price')
# If p_value = 0.02 → Drift detected (price distribution changed)
```

### 2. Population Stability Index (PSI)
**What it does**: Measures how much a population has shifted  
**Best for**: Finding subtle distribution changes over time  
**Thresholds**:
- **PSI < 0.10**: No significant change
- **PSI 0.10-0.25**: Small population change (monitor)
- **PSI > 0.25**: Significant change (drift detected)

**Example**:
```python
psi = engine.population_stability_index(current_data, 'rsi')
# If PSI = 0.28 → Significant drift detected
```

### 3. Wasserstein Distance
**What it does**: Compares "distance" between two probability distributions  
**Best for**: Detecting distribution shape changes  
**Interpretation**:
- **Lower values**: Distributions are similar
- **Higher values**: Distributions are different

**Example**:
```python
distance = engine.wasserstein_distance(current_data, 'macd')
# If distance = 0.15 → Moderate drift detected
```

### 4. Chi-Square Test
**What it does**: Tests if categorical variable distributions differ  
**Best for**: Categorical features (trend direction, market conditions)  
**Interpretation**:
- **p-value > 0.05**: No drift
- **p-value ≤ 0.05**: Drift detected

**Example**:
```python
chi2_stat, p_value = engine.chi_square_test(current_data, 'trend')
# If p_value = 0.01 → Trend distribution has drifted
```

---

## Setting Up Drift Detection

### Step 1: Initialize Engine
```python
from src.data_drift_detection import DriftDetectionEngine
import pandas as pd

# Load baseline/reference data (e.g., last 365 days)
reference_data = pd.read_csv('data/raw/bitcoin_timeseries.csv').head(365)

# Initialize engine with custom thresholds
engine = DriftDetectionEngine(
    reference_data=reference_data,
    threshold_ks=0.05,           # KS test threshold
    threshold_psi=0.25,          # PSI threshold
    threshold_wasserstein=0.1,   # Wasserstein threshold
    reference_period="2024-12-01"
)
```

### Step 2: Check for Drift
```python
# Load current data
current_data = pd.read_csv('data/raw/bitcoin_timeseries.csv').tail(30)

# Run comprehensive drift detection
report = engine.detect_drift(current_data)

# Print report
print(report.summary())
```

### Step 3: Analyze Results
```python
# Check if drift detected
if report.drift_detected:
    print(f"⚠️  Drift Detected! Severity: {report.overall_severity}")
    
    # View specific test results
    print("KS Test Results:")
    for column, result in report.ks_tests.items():
        if result['drift_detected']:
            print(f"  {column}: p-value = {result['p_value']}")
    
    # View PSI results
    print("PSI Results:")
    for column, result in report.psi_tests.items():
        if result['drift_detected']:
            print(f"  {column}: PSI = {result['psi']} (Severity: {result['severity']})")

else:
    print("✅ No drift detected - data distribution stable")
```

---

## Automated Drift Checking

### Daily Drift Check (Cron Job)
```bash
# Add to crontab (runs daily at 3 AM UTC)
0 3 * * * cd /path/to/project && python -m scripts.check_drift_daily

# Or use Windows Task Scheduler:
# Program: python.exe
# Arguments: -m scripts.check_drift_daily
# Working Directory: C:\path\to\project
```

### Drift Check Script
```python
# scripts/check_drift_daily.py
from src.data_drift_detection import DriftDetectionEngine
import pandas as pd
import json
from datetime import datetime

# Load baseline data
reference = pd.read_csv('models/reference_data_baseline.csv')

# Initialize engine
engine = DriftDetectionEngine(reference_data=reference)

# Load today's data
today_data = pd.read_csv('data/raw/bitcoin_timeseries.csv').tail(7)

# Run drift detection
report = engine.detect_drift(today_data)

# Save report
with open(f'reports/drift_reports/{datetime.now().strftime("%Y%m%d")}_report.json', 'w') as f:
    json.dump(report.to_dict(), f, indent=2, default=str)

# Alert if drift detected
if report.drift_detected:
    print(f"🚨 DRIFT DETECTED: {report.overall_severity}")
    # Send alert (email, Slack, Discord)
else:
    print("✅ No drift detected")
```

---

## Integration with CI/CD Pipeline

### GitHub Actions Workflow (ml-tests.yml)
```yaml
drift-detection:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run drift detection tests
      run: |
        pytest tests/test_data_drift.py -v --tb=short
    
    - name: Check for data drift
      run: python -m scripts.check_drift_daily
    
    - name: Upload drift report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: drift-reports
        path: reports/drift_reports/
```

---

## Monitoring Metrics

### Key Metrics to Track

| Metric | Threshold | Warning | Critical |
|--------|-----------|---------|----------|
| **KS Test p-value** | > 0.05 | 0.02-0.05 | < 0.02 |
| **PSI Value** | < 0.10 | 0.10-0.25 | > 0.25 |
| **Wasserstein Distance** | < 0.05 | 0.05-0.10 | > 0.10 |
| **Chi-Square p-value** | > 0.05 | 0.02-0.05 | < 0.02 |

### Performance Tracking
```python
# Track drift over time
drift_history = []

for period in date_ranges:
    data = load_data(period)
    report = engine.detect_drift(data)
    drift_history.append({
        'period': period,
        'drift_detected': report.drift_detected,
        'severity': report.overall_severity,
        'timestamp': datetime.now()
    })

# Plot trend
import matplotlib.pyplot as plt
dates = [h['period'] for h in drift_history]
severities = [1 if h['drift_detected'] else 0 for h in drift_history]
plt.plot(dates, severities)
plt.title('Data Drift Over Time')
plt.show()
```

---

## Alert Configuration

### Drift Alert Thresholds
```python
# alert_manager.py integration
DRIFT_ALERTS = {
    'critical': {
        'psi': 0.30,
        'ks_p_value': 0.01,
        'wasserstein': 0.15,
        'action': 'IMMEDIATE_INVESTIGATION'
    },
    'warning': {
        'psi': 0.20,
        'ks_p_value': 0.05,
        'wasserstein': 0.10,
        'action': 'SCHEDULE_INVESTIGATION'
    },
    'info': {
        'psi': 0.10,
        'ks_p_value': 0.10,
        'wasserstein': 0.05,
        'action': 'LOG_MONITOR'
    }
}
```

### Alert Escalation
```
Level 1 (Monitor):
  → Log drift detection
  → Add to daily report
  → Action: Continue monitoring

Level 2 (Warning):
  → Send Slack notification
  → Create investigation ticket
  → Action: Review within 24 hours

Level 3 (Critical):
  → Page on-call engineer
  → Stop new model deployments
  → Trigger emergency retraining
  → Action: Immediate investigation
```

---

## Interpreting Drift Reports

### Example Report Output
```
======================================================================
DATA DRIFT DETECTION REPORT
======================================================================

Reference Period: 2024-12-01 (365 records)
Current Period:   2024-12-05 (7 records)
Timestamp:        2024-12-05T10:30:00

OVERALL VERDICT: ✅ NO DRIFT DETECTED
Severity Level:   LOW

📊 Kolmogorov-Smirnov Tests (3 features):
   btc_price          ✅ OK                 (p=0.12)
   volume             ✅ OK                 (p=0.34)
   rsi                ✅ OK                 (p=0.56)

📈 Wasserstein Distance Tests (3 features):
   btc_price          ✅ OK                 (dist=0.045)
   volume             ✅ OK                 (dist=0.032)
   rsi                ✅ OK                 (dist=0.021)

📉 Population Stability Index (3 features):
   btc_price          ✅ OK                 (PSI=0.065)
   volume             ✅ OK                 (PSI=0.082)
   rsi                ✅ OK                 (PSI=0.095)

======================================================================
```

### What Different Results Mean

**✅ All Green (No Drift)**
- Data is stable and consistent with baseline
- Model should continue to perform well
- Action: Continue normal operations

**⚠️ Some Yellow (Partial Drift)**
- Some features show drift, but not critical
- Monitor closely over next few days
- Consider retraining if trend continues
- Action: Schedule investigation within 24 hours

**🚨 Red (Drift Detected)**
- Clear statistical evidence of distribution change
- Model performance likely degraded
- Immediate investigation required
- Action: Stop deployments, investigate root cause

---

## Troubleshooting

### Problem: High False Positive Rate
**Cause**: Thresholds too strict  
**Solution**: 
```python
# Increase thresholds
engine = DriftDetectionEngine(
    reference_data=reference,
    threshold_ks=0.10,      # Increased from 0.05
    threshold_psi=0.35,     # Increased from 0.25
    threshold_wasserstein=0.15
)
```

### Problem: Missing Drift Detection
**Cause**: Thresholds too loose  
**Solution**:
```python
# Decrease thresholds
engine = DriftDetectionEngine(
    reference_data=reference,
    threshold_ks=0.02,      # Decreased from 0.05
    threshold_psi=0.15,     # Decreased from 0.25
    threshold_wasserstein=0.05
)
```

### Problem: Inconsistent Reference Data
**Cause**: Reference period unrepresentative  
**Solution**:
```python
# Use longer reference period
reference = load_last_n_days(days=90)  # Use 3 months instead of 1 month
engine = DriftDetectionEngine(reference_data=reference)
```

### Problem: High Computational Cost
**Cause**: Large datasets  
**Solution**:
```python
# Sample data for faster computation
sample_size = min(1000, len(data))
sampled_data = data.sample(n=sample_size, random_state=42)

# Parallel drift detection
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(engine.ks_test, columns))
```

---

## Best Practices

### 1. **Update Reference Data Regularly**
- Update baseline every quarter
- Include seasonal variations
- Document reference period clearly

### 2. **Use Multiple Detection Methods**
- Never rely on single test
- Combine KS, PSI, and Wasserstein
- Use voting mechanism

### 3. **Track Drift History**
```python
# Keep last 90 days of drift reports
drift_reports = []
for date in last_90_days:
    report = load_report(date)
    drift_reports.append(report)

# Analyze trends
drift_trend = analyze_trend(drift_reports)
if drift_trend == 'increasing':
    print("⚠️  Drift increasing - proactive retraining recommended")
```

### 4. **Alert with Context**
```python
# Include context in alerts
alert = {
    'drift_detected': True,
    'severity': 'HIGH',
    'features_affected': ['price', 'volume'],
    'likely_cause': 'Market volatility spike',
    'recommended_action': 'Retrain with new data',
    'urgency': 'IMMEDIATE'
}
```

### 5. **Document Root Causes**
- Log external events (market crashes, regulatory changes)
- Correlate drift with external factors
- Build drift cause database

---

## Next Steps

1. ✅ **Run baseline drift detection**
   ```bash
   python -m src.data_drift_detection
   ```

2. ✅ **Run automated tests**
   ```bash
   pytest tests/test_data_drift.py -v
   ```

3. ✅ **Set up daily monitoring**
   - Add drift check to scheduled-training workflow
   - Configure alerts in alert_manager.py

4. ✅ **Monitor first week**
   - Check daily reports
   - Validate thresholds
   - Adjust if needed

5. ✅ **Integrate with dashboards**
   - GitHub Actions dashboard
   - Slack/Discord notifications
   - Custom monitoring dashboard

---

## Quick Reference

### Commands
```bash
# Run drift detection
python -m src.data_drift_detection

# Run tests
pytest tests/test_data_drift.py -v

# Check specific file
python -c "from src.data_drift_detection import compare_datasets; print(compare_datasets('ref.csv', 'curr.csv').summary())"

# Daily scheduled check
python scripts/check_drift_daily.py
```

### Key Files
- **src/data_drift_detection.py** - Core drift detection module
- **tests/test_data_drift.py** - Comprehensive test suite
- **alert_manager.py** - Alert thresholds and notifications
- **.github/workflows/ml-tests.yml** - CI/CD integration

---

**Last Updated**: December 5, 2024  
**Status**: ✅ Ready for Production
