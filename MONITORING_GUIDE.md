# 📊 Post-Deployment Monitoring Guide

## Overview

After deploying the CI/CD pipeline, continuous monitoring ensures system health, performance optimization, and early issue detection. This guide covers all aspects of monitoring your ML pipeline.

---

## 🎯 Monitoring Objectives

```
✅ Track pipeline execution health
✅ Monitor model performance metrics
✅ Detect anomalies and degradation
✅ Ensure security compliance
✅ Optimize resource usage
✅ Enable quick debugging
✅ Maintain audit trails
```

---

## 📈 Key Metrics to Monitor

### **1. Pipeline Health Metrics**

#### Success Rate
```bash
# What to track
- CI Pipeline success rate (target: >95%)
- ML Tests success rate (target: >95%)
- CD Pipeline success rate (target: >95%)
- Overall pipeline success rate (target: >95%)

# How to check
gh run list --limit 50 | grep -c "COMPLETED"
# Divide by total runs
```

#### Execution Time
```bash
# What to track
- CI execution time (target: 3-5 min)
- ML Tests execution time (target: 5-8 min)
- CD execution time (target: 10-25 min)
- Daily training time (target: 15-30 min)

# How to check
gh run view <run-id> --json duration
```

#### Job-Level Metrics
```bash
# What to track
- Each job's pass/fail status
- Job execution time
- Job resource usage
- Failed step identification

# How to check
gh run view <run-id> --json jobs
```

---

### **2. Model Performance Metrics**

#### Classification Metrics
```
Accuracy (target: ≥65%)
  └─ Percentage of correct predictions
  
F1 Score (target: ≥0.65)
  └─ Balance between precision & recall
  
Precision (target: ≥0.65)
  └─ Correctness of positive predictions
  
Recall (target: ≥0.60)
  └─ Coverage of positive class
```

#### Regression Metrics
```
RMSE (Root Mean Squared Error)
  └─ Lower is better (target: <1.5)
  
R² Score (Coefficient of Determination)
  └─ Higher is better (target: >0.1)
```

#### Performance Tracking
```bash
# Location of metrics
models/manifest.json          # Latest model versions
models/v*_metadata.json       # Individual model metrics
performance_history.jsonl     # Daily performance history
```

#### Monitoring Script
```python
import json
import os
from collections import deque

def track_performance():
    """Extract and track model metrics"""
    models_dir = 'models/'
    
    # Get latest metadata
    json_files = sorted([f for f in os.listdir(models_dir) 
                        if 'metadata' in f and f.endswith('.json')])
    
    if json_files:
        latest = os.path.join(models_dir, json_files[-1])
        with open(latest) as f:
            metrics = json.load(f)
        
        print("Latest Model Metrics:")
        print(f"  Accuracy: {metrics.get('accuracy', 'N/A')}")
        print(f"  F1 Score: {metrics.get('f1_score', 'N/A')}")
        print(f"  RMSE: {metrics.get('rmse', 'N/A')}")
        
        # Check thresholds
        if metrics.get('accuracy', 0) < 0.65:
            print("⚠️  WARNING: Accuracy below threshold!")
        
        return metrics
```

---

### **3. Data Quality Metrics**

#### Data Freshness
```bash
# What to track
- Last data update timestamp
- Data age (should be < 24 hours)
- API fetch success rate

# How to check
ls -lt data/raw/bitcoin_timeseries.csv | head -1
stat data/raw/bitcoin_timeseries.csv  # Check modification time
```

#### Data Completeness
```bash
# What to track
- Number of records (target: 365)
- Missing values (target: 0)
- Null values (target: 0)
- Data type consistency

# Validation script
python -c "
import pandas as pd
df = pd.read_csv('data/raw/bitcoin_timeseries.csv')
print(f'Records: {len(df)}')
print(f'Missing: {df.isnull().sum().sum()}')
print(f'Columns: {df.shape[1]}')
"
```

#### Data Consistency
```bash
# Check for duplicates
python -c "
import pandas as pd
df = pd.read_csv('data/raw/bitcoin_timeseries.csv')
dupes = df.duplicated().sum()
print(f'Duplicates: {dupes}')
"

# Check date range
python -c "
import pandas as pd
df = pd.read_csv('data/raw/bitcoin_timeseries.csv')
df['date'] = pd.to_datetime(df['date'])
print(f'Date range: {df[\"date\"].min()} to {df[\"date\"].max()}')
"
```

---

### **4. Resource Usage Metrics**

#### GitHub Actions Usage
```bash
# What to track
- Minutes used this month
- Limit: 2,000 min/month (private repos)
- Projected usage based on current runs

# How to check via CLI
gh api user/repos -H "Accept: application/vnd.github+json" | \
  jq '.[] | select(.name=="your-repo") | .owner'

# Or via GitHub UI
Settings → Billing and plans → Actions
```

#### Artifact Storage
```bash
# What to track
- Artifact size (target: minimize)
- Storage usage trend
- Retention policy compliance

# Monitor by checking
Actions tab → Artifacts → Size
```

#### Build Time Trends
```bash
# Track optimization over time
gh run list --limit 100 | \
  awk '{print $NF}' | \
  sort | \
  uniq -c | \
  tail -20
```

---

## 🔍 Monitoring Dashboard Setup

### **Option 1: GitHub Native Dashboard**

**Location**: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

**What to Monitor:**
```
✅ All Workflows tab
   └─ View all workflow runs
   
✅ Individual Workflow tabs
   ├─ CI pipeline runs
   ├─ ML Tests runs
   ├─ CD pipeline runs
   └─ Scheduled training runs
   
✅ Workflow file status
   └─ Any syntax errors
   
✅ Branch status checks
   └─ Pass/fail requirements
```

**Key Indicators:**
```
🟢 Green checkmark   = All passed
🟡 Yellow dot        = Running
🔴 Red X             = Failed
⚫ Gray dot          = Skipped/Cancelled
```

---

### **Option 2: Local Monitoring Script**

Create `monitor_pipeline.py`:

```python
#!/usr/bin/env python3
"""
CI/CD Pipeline Monitoring Script
Provides real-time status of pipeline health
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict

def get_recent_runs(limit=20):
    """Get recent workflow runs using GitHub CLI"""
    try:
        result = subprocess.run(
            ['gh', 'run', 'list', '--limit', str(limit), '--json',
             'name,status,conclusion,createdAt,databaseId'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching runs: {e}")
    return []

def calculate_success_rate(runs):
    """Calculate pipeline success rate"""
    if not runs:
        return 0.0
    
    successful = sum(1 for r in runs if r.get('conclusion') == 'success')
    return (successful / len(runs)) * 100

def get_model_metrics():
    """Get latest model performance metrics"""
    models_dir = 'models/'
    metrics = {}
    
    if os.path.exists(models_dir):
        # Read latest metadata
        json_files = sorted([
            f for f in os.listdir(models_dir)
            if 'metadata' in f and f.endswith('.json')
        ])
        
        if json_files:
            latest = os.path.join(models_dir, json_files[-1])
            with open(latest) as f:
                metrics = json.load(f)
    
    return metrics

def check_data_freshness():
    """Check if data is recent"""
    data_file = 'data/raw/bitcoin_timeseries.csv'
    
    if os.path.exists(data_file):
        mod_time = os.path.getmtime(data_file)
        mod_datetime = datetime.fromtimestamp(mod_time)
        age_hours = (datetime.now() - mod_datetime).total_seconds() / 3600
        
        return {
            'last_updated': mod_datetime.isoformat(),
            'age_hours': age_hours,
            'fresh': age_hours < 24
        }
    
    return {'fresh': False, 'error': 'Data file not found'}

def print_status_report():
    """Print comprehensive status report"""
    print("\n" + "="*70)
    print(f"  CI/CD PIPELINE MONITORING REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Pipeline Health
    print("📊 PIPELINE HEALTH")
    print("-" * 70)
    runs = get_recent_runs(50)
    
    if runs:
        success_rate = calculate_success_rate(runs)
        print(f"  Success Rate (last 50 runs): {success_rate:.1f}%")
        print(f"  Status Target: >95%")
        
        if success_rate >= 95:
            print(f"  ✅ HEALTHY")
        elif success_rate >= 85:
            print(f"  ⚠️  WARNING")
        else:
            print(f"  ❌ CRITICAL")
        
        # Recent failures
        failures = [r for r in runs if r.get('conclusion') != 'success']
        if failures:
            print(f"\n  Recent Failures:")
            for f in failures[:3]:
                print(f"    • {f.get('name')} - {f.get('conclusion')}")
    
    # Model Performance
    print("\n📈 MODEL PERFORMANCE")
    print("-" * 70)
    metrics = get_model_metrics()
    
    if metrics:
        print(f"  Accuracy: {metrics.get('accuracy', 'N/A')}")
        print(f"  Target: ≥65%")
        
        accuracy = metrics.get('accuracy', 0)
        if accuracy >= 0.65:
            print(f"  ✅ PASSING")
        else:
            print(f"  ⚠️  BELOW THRESHOLD")
        
        print(f"\n  F1 Score: {metrics.get('f1_score', 'N/A')}")
        print(f"  RMSE: {metrics.get('rmse', 'N/A')}")
        print(f"  Training Samples: {metrics.get('training_samples', 'N/A')}")
        print(f"  Test Samples: {metrics.get('test_samples', 'N/A')}")
    
    # Data Freshness
    print("\n🗂️  DATA QUALITY")
    print("-" * 70)
    data_info = check_data_freshness()
    
    if data_info.get('fresh'):
        print(f"  ✅ DATA FRESH")
    else:
        print(f"  ⚠️  DATA STALE")
    
    print(f"  Last Updated: {data_info.get('last_updated', 'Unknown')}")
    print(f"  Age: {data_info.get('age_hours', 'Unknown')} hours")
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    
    status = "✅ HEALTHY" if success_rate >= 95 else "⚠️  NEEDS ATTENTION"
    print(f"  Overall Status: {status}")
    print(f"  Next Steps: Check GitHub Actions for details")
    print("="*70 + "\n")

if __name__ == '__main__':
    print_status_report()
```

**Usage:**
```bash
python monitor_pipeline.py

# Run continuously
while true; do python monitor_pipeline.py; sleep 300; done
```

---

## 🚨 Alert Conditions

### **Critical Alerts** (Immediate Action Required)

```
🔴 CRITICAL - Pipeline Failure
   └─ Multiple consecutive failed runs
   └─ Action: Check logs, investigate immediately

🔴 CRITICAL - Model Accuracy Degradation >10%
   └─ Accuracy drops from 70% to 60%
   └─ Action: Review training data, retrain

🔴 CRITICAL - Security Vulnerabilities Found
   └─ Trivy scan detects high-severity issues
   └─ Action: Review and patch immediately

🔴 CRITICAL - Data Missing or Corrupted
   └─ Data validation fails
   └─ Action: Check data source, restore backup
```

### **Warning Alerts** (Review & Monitor)

```
🟡 WARNING - Success Rate < 90%
   └─ Action: Review failed runs, optimize

🟡 WARNING - Model Accuracy < 65%
   └─ Action: Review model, consider retraining

🟡 WARNING - Data Age > 24 hours
   └─ Action: Check API, verify schedule

🟡 WARNING - Build Time > 30 minutes
   └─ Action: Optimize workflows, cache layers

🟡 WARNING - Artifact Storage > 80% quota
   └─ Action: Clean old artifacts, increase retention
```

### **Info Alerts** (For Tracking)

```
ℹ️  INFO - Successful pipeline run
   └─ Record metrics, update performance history

ℹ️  INFO - Scheduled daily training complete
   └─ Log results, check metrics

ℹ️  INFO - Weekly performance summary
   └─ Review trends, plan optimizations
```

---

## 📋 Daily Monitoring Checklist

### **Morning Check (5 minutes)**
```
☐ Check GitHub Actions dashboard
☐ Verify all scheduled runs completed
☐ Review model accuracy metrics
☐ Check for any red/failed indicators
☐ Note any issues to investigate
```

### **Daily Routine (10 minutes)**
```
☐ Run monitoring script
☐ Check pipeline success rate
☐ Verify data freshness (< 24 hrs old)
☐ Review recent model metrics
☐ Check artifact storage usage
☐ Monitor build time trends
```

### **Weekly Review (30 minutes)**
```
☐ Generate performance report
☐ Analyze trends (accuracy, time, success)
☐ Review failed runs and root causes
☐ Check security alerts
☐ Update documentation if needed
☐ Plan optimizations
```

### **Monthly Deep Dive (1 hour)**
```
☐ Complete system audit
☐ Review all metrics trends
☐ Analyze resource usage
☐ Check for performance improvements
☐ Update baselines and targets
☐ Plan next optimizations
```

---

## 📊 Performance Tracking

### **Create Performance Dashboard**

```python
import pandas as pd
import json
from datetime import datetime, timedelta

def create_performance_report():
    """Generate performance report from history"""
    
    # Read performance history
    history = []
    if os.path.exists('performance_history.jsonl'):
        with open('performance_history.jsonl') as f:
            for line in f:
                history.append(json.loads(line))
    
    if not history:
        return None
    
    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = df[df['timestamp'] > week_ago]
    
    report = {
        'period': 'Last 7 Days',
        'runs': len(recent),
        'avg_accuracy': recent['accuracy'].mean(),
        'max_accuracy': recent['accuracy'].max(),
        'min_accuracy': recent['accuracy'].min(),
        'avg_f1': recent['f1_score'].mean(),
        'trend': 'improving' if recent['accuracy'].iloc[-1] > recent['accuracy'].iloc[0] else 'declining'
    }
    
    print(f"Performance Report - {report['period']}")
    print(f"  Runs: {report['runs']}")
    print(f"  Avg Accuracy: {report['avg_accuracy']:.4f}")
    print(f"  Max Accuracy: {report['max_accuracy']:.4f}")
    print(f"  Min Accuracy: {report['min_accuracy']:.4f}")
    print(f"  Trend: {report['trend']}")
    
    return report
```

---

## 🔔 Notification Setup

### **Discord Notifications** (Already Configured)

```bash
# Set webhook
$env:DISCORD_WEBHOOK_URL = "your-webhook-url"

# Test notification
python -c "
import requests
import os

webhook = os.getenv('DISCORD_WEBHOOK_URL')
if webhook:
    requests.post(webhook, json={
        'content': '✅ Pipeline monitoring active!'
    })
"
```

### **Slack Integration** (Optional)

```bash
# Set webhook
$env:SLACK_WEBHOOK_URL = "your-slack-webhook"

# Send notification
python -c "
import requests
import os

slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
if slack_webhook:
    requests.post(slack_webhook, json={
        'text': '✅ Pipeline monitoring active!',
        'attachments': [{
            'color': 'good',
            'fields': [
                {'title': 'Status', 'value': 'Running', 'short': True}
            ]
        }]
    })
"
```

### **Email Alerts** (Optional)

```bash
# Configure in GitHub
Settings → Notifications → Email
  ✓ Receive email notifications for workflow runs
```

---

## 📈 Metrics Collection

### **Automated Metrics Logging**

The scheduled workflow automatically logs:
- Daily training timestamp
- Model accuracy
- F1 score
- RMSE
- R² score
- Training/test sample counts

Location: `performance_history.jsonl`

### **Manual Metrics Export**

```bash
# Export metrics to CSV
python -c "
import json
import pandas as pd

history = []
with open('performance_history.jsonl') as f:
    for line in f:
        history.append(json.loads(line))

df = pd.DataFrame(history)
df.to_csv('performance_metrics.csv', index=False)
print(f'Exported {len(df)} records')
"
```

---

## 🔧 Troubleshooting Monitoring Issues

### **"GitHub CLI not installed"**
```bash
# Install GitHub CLI
# Windows with Scoop:
scoop install gh

# Verify
gh --version
gh auth login  # Authenticate if needed
```

### **"Can't access artifact data"**
```bash
# Check permissions
gh auth status

# Verify token has repo access
gh auth refresh --scopes repo
```

### **"Performance history not found"**
```bash
# Create empty history file to start
touch performance_history.jsonl

# Or initialize from existing metrics
python -c "
import json
import os

# Read latest model metadata
models_dir = 'models/'
json_files = sorted([f for f in os.listdir(models_dir) 
                    if 'metadata' in f])
if json_files:
    with open(os.path.join(models_dir, json_files[-1])) as f:
        metrics = json.load(f)
    # Append to history
    with open('performance_history.jsonl', 'a') as f:
        f.write(json.dumps(metrics) + '\n')
"
```

---

## 📊 Dashboard Tools (Optional)

### **Grafana** (Advanced)
```
1. Install Grafana
2. Connect to GitHub API data source
3. Create dashboards for:
   - Pipeline success rate
   - Model accuracy trends
   - Build time trends
   - Resource usage
```

### **Prometheus** (Advanced)
```
1. Export metrics in Prometheus format
2. Scrape GitHub Actions API
3. Set up alerting rules
4. Visualize in Grafana
```

### **Google Sheets** (Simple)
```
1. Create spreadsheet
2. Manually update daily:
   - Run date
   - Success rate
   - Model accuracy
   - Any issues
3. Create charts for trends
```

---

## 📋 Monitoring Schedule

```
REAL-TIME (continuous)
  ├─ GitHub Actions dashboard
  └─ Critical alerts

HOURLY (automated)
  ├─ Log metrics to history
  └─ Check for failures

DAILY (manual + automated)
  ├─ Morning status check
  ├─ Scheduled training execution
  ├─ Performance tracking
  └─ Alert review

WEEKLY (manual)
  ├─ Comprehensive review
  ├─ Trend analysis
  ├─ Performance report
  └─ Optimization planning

MONTHLY (manual)
  ├─ Full system audit
  ├─ Baseline updates
  ├─ Documentation update
  └─ Next quarter planning
```

---

## 🎯 Success Criteria

| Metric | Target | Status |
|--------|--------|--------|
| CI Success Rate | >95% | Monitor |
| ML Tests Success Rate | >95% | Monitor |
| CD Success Rate | >95% | Monitor |
| Model Accuracy | ≥65% | Monitor |
| Build Time | <30 min | Optimize |
| Data Freshness | <24 hrs | Track |
| Artifact Storage | <80% quota | Manage |
| Security Alerts | 0 critical | Monitor |

---

## 📞 Quick Commands Reference

```bash
# Check status
gh run list

# View specific run
gh run view <id>

# View logs
gh run view <id> --log

# Get workflows
gh workflow list

# Trigger workflow
gh workflow run scheduled-training.yml

# Monitor performance
python monitor_pipeline.py

# Export metrics
python -c "
import pandas as pd
import json
history = [json.loads(line) for line in open('performance_history.jsonl')]
pd.DataFrame(history).to_csv('metrics.csv')
"
```

---

## 🚀 Post-Deployment Monitoring Checklist

### **Week 1: Initial Setup**
- [ ] Access GitHub Actions dashboard
- [ ] Install GitHub CLI
- [ ] Run first monitoring script
- [ ] Set up Discord/Slack notifications
- [ ] Review first week of metrics
- [ ] Document baseline performance

### **Month 1: Stabilization**
- [ ] Daily monitoring routine established
- [ ] All alerts configured
- [ ] Performance baselines recorded
- [ ] Weekly reports generated
- [ ] No critical issues remaining
- [ ] Team trained on monitoring

### **Ongoing: Maintenance**
- [ ] Daily health checks
- [ ] Weekly performance reviews
- [ ] Monthly deep dives
- [ ] Quarterly optimizations
- [ ] Annual planning updates

---

**Status**: ✅ **MONITORING READY**

All monitoring components configured and documented!
