#!/usr/bin/env python3
"""
CI/CD Pipeline Monitoring Script
Real-time pipeline health and performance monitoring
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


class PipelineMonitor:
    """Monitor CI/CD pipeline health and metrics"""
    
    def __init__(self):
        self.models_dir = 'models/'
        self.data_dir = 'data/raw/'
        self.history_file = 'performance_history.jsonl'
    
    def get_recent_runs(self, limit=30):
        """Fetch recent workflow runs from GitHub CLI"""
        try:
            cmd = [
                'gh', 'run', 'list',
                '--limit', str(limit),
                '--json', 'name,status,conclusion,createdAt,databaseId'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"⚠️  GitHub CLI error: {result.stderr}")
                return []
        except FileNotFoundError:
            print("❌ GitHub CLI not found. Install with: scoop install gh")
            return []
        except Exception as e:
            print(f"❌ Error fetching runs: {e}")
            return []
    
    def calculate_success_rate(self, runs):
        """Calculate pipeline success rate"""
        if not runs:
            return 0.0
        
        successful = sum(1 for r in runs if r.get('conclusion') == 'success')
        return (successful / len(runs)) * 100
    
    def get_model_metrics(self):
        """Get latest model performance metrics"""
        if not os.path.exists(self.models_dir):
            return {}
        
        json_files = sorted([
            f for f in os.listdir(self.models_dir)
            if 'metadata' in f and f.endswith('.json')
        ])
        
        if not json_files:
            return {}
        
        try:
            latest = os.path.join(self.models_dir, json_files[-1])
            with open(latest) as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading metrics: {e}")
            return {}
    
    def check_data_freshness(self):
        """Check if data is recent"""
        data_file = os.path.join(self.data_dir, 'bitcoin_timeseries.csv')
        
        if not os.path.exists(data_file):
            return {
                'fresh': False,
                'error': 'Data file not found',
                'last_updated': None,
                'age_hours': None
            }
        
        try:
            mod_time = os.path.getmtime(data_file)
            mod_datetime = datetime.fromtimestamp(mod_time)
            age_hours = (datetime.now() - mod_datetime).total_seconds() / 3600
            
            return {
                'fresh': age_hours < 24,
                'last_updated': mod_datetime.isoformat(),
                'age_hours': age_hours,
                'file_size_mb': os.path.getsize(data_file) / (1024 * 1024)
            }
        except Exception as e:
            print(f"⚠️  Error checking data: {e}")
            return {'fresh': False, 'error': str(e)}
    
    def get_artifact_size(self):
        """Estimate artifact storage usage"""
        if not os.path.exists(self.models_dir):
            return 0.0
        
        total_size = 0
        for root, dirs, files in os.walk(self.models_dir):
            for file in files:
                total_size += os.path.getsize(os.path.join(root, file))
        
        return total_size / (1024 * 1024)  # MB
    
    def get_performance_trend(self):
        """Analyze performance trend from history"""
        if not os.path.exists(self.history_file):
            return None
        
        try:
            history = []
            with open(self.history_file) as f:
                for line in f:
                    history.append(json.loads(line))
            
            if len(history) < 2:
                return None
            
            # Last 7 runs
            recent = history[-7:] if len(history) >= 7 else history
            
            if recent:
                current_acc = recent[-1].get('accuracy', 0)
                prev_acc = recent[0].get('accuracy', 0)
                change = (current_acc - prev_acc) * 100
                
                return {
                    'runs_tracked': len(history),
                    'current_accuracy': current_acc,
                    'change_percent': change,
                    'trend': 'improving' if change >= 0 else 'declining'
                }
        except Exception as e:
            print(f"⚠️  Error analyzing trends: {e}")
        
        return None
    
    def print_status_header(self):
        """Print report header"""
        print("\n" + "=" * 75)
        print(f"  🔍 CI/CD PIPELINE MONITORING REPORT")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 75 + "\n")
    
    def print_pipeline_health(self, runs):
        """Print pipeline health section"""
        print("📊 PIPELINE HEALTH")
        print("-" * 75)
        
        if not runs:
            print("  ❌ No recent runs found")
            print("     Install GitHub CLI: scoop install gh")
            return
        
        success_rate = self.calculate_success_rate(runs)
        
        print(f"  Last 30 runs: {len(runs)}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Target: >95%")
        print()
        
        # Status indicator
        if success_rate >= 95:
            status = "✅ HEALTHY"
        elif success_rate >= 85:
            status = "⚠️  WARNING"
        else:
            status = "❌ CRITICAL"
        print(f"  Status: {status}")
        
        # Recent failures
        failures = [r for r in runs if r.get('conclusion') != 'success']
        if failures:
            print(f"\n  Recent Issues ({len(failures)}):")
            for f in failures[:3]:
                workflow = f.get('name', 'Unknown')
                conclusion = f.get('conclusion', 'unknown')
                print(f"    • {workflow} - {conclusion}")
    
    def print_model_performance(self, metrics):
        """Print model performance section"""
        print("\n📈 MODEL PERFORMANCE")
        print("-" * 75)
        
        if not metrics:
            print("  ℹ️  No model metrics available yet")
            return
        
        accuracy = metrics.get('accuracy', 0)
        f1_score = metrics.get('f1_score', 0)
        rmse = metrics.get('rmse', 0)
        
        print(f"  Accuracy: {accuracy:.4f} (target: ≥0.65)")
        print(f"  F1 Score: {f1_score:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        print()
        
        # Status
        if accuracy >= 0.65:
            status = "✅ PASSING"
        else:
            status = "⚠️  BELOW THRESHOLD"
        print(f"  Status: {status}")
        
        # Additional metrics
        if 'training_samples' in metrics:
            print(f"\n  Training Samples: {metrics['training_samples']}")
        if 'test_samples' in metrics:
            print(f"  Test Samples: {metrics['test_samples']}")
    
    def print_data_quality(self, data_info):
        """Print data quality section"""
        print("\n🗂️  DATA QUALITY")
        print("-" * 75)
        
        if data_info.get('error'):
            print(f"  ⚠️  {data_info['error']}")
            return
        
        fresh = data_info.get('fresh', False)
        last_updated = data_info.get('last_updated', 'Unknown')
        age_hours = data_info.get('age_hours', -1)
        file_size = data_info.get('file_size_mb', 0)
        
        status = "✅ FRESH" if fresh else "⚠️  STALE"
        print(f"  Status: {status}")
        print(f"  Last Updated: {last_updated}")
        print(f"  Age: {age_hours:.1f} hours (target: <24)")
        print(f"  File Size: {file_size:.2f} MB")
    
    def print_resource_usage(self):
        """Print resource usage section"""
        print("\n💾 RESOURCE USAGE")
        print("-" * 75)
        
        artifact_size = self.get_artifact_size()
        print(f"  Artifact Storage: {artifact_size:.2f} MB")
        print(f"  Models Directory: {self.models_dir}")
        
        if artifact_size > 500:  # Warning if > 500MB
            print(f"  ⚠️  Storage usage is high")
    
    def print_performance_trend(self):
        """Print performance trend section"""
        print("\n📊 PERFORMANCE TREND")
        print("-" * 75)
        
        trend = self.get_performance_trend()
        
        if not trend:
            print("  ℹ️  Insufficient history data")
            return
        
        print(f"  Runs Tracked: {trend['runs_tracked']}")
        print(f"  Current Accuracy: {trend['current_accuracy']:.4f}")
        
        if trend['change_percent'] >= 0:
            print(f"  Change: +{trend['change_percent']:.2f}% ({trend['trend']})")
        else:
            print(f"  Change: {trend['change_percent']:.2f}% ({trend['trend']})")
        
        # Trend indicator
        if trend['trend'] == 'improving':
            print(f"  ✅ Trend: IMPROVING")
        else:
            print(f"  ⚠️  Trend: DECLINING")
    
    def print_summary(self, runs):
        """Print summary and recommendations"""
        print("\n" + "=" * 75)
        print("📋 SUMMARY & RECOMMENDATIONS")
        print("=" * 75)
        
        if not runs:
            print("  ℹ️  Unable to determine status without recent runs")
            print("  → Ensure GitHub CLI is installed and authenticated")
            print("  → Check: gh auth status")
            return
        
        success_rate = self.calculate_success_rate(runs)
        metrics = self.get_model_metrics()
        data_info = self.check_data_freshness()
        
        issues = []
        
        # Check success rate
        if success_rate < 95:
            issues.append("Low pipeline success rate")
        
        # Check model accuracy
        if metrics.get('accuracy', 1) < 0.65:
            issues.append("Model accuracy below threshold")
        
        # Check data freshness
        if not data_info.get('fresh', False):
            issues.append("Data is stale (>24 hours old)")
        
        if issues:
            print(f"\n  ⚠️  Issues Found ({len(issues)}):")
            for issue in issues:
                print(f"    • {issue}")
        else:
            print("\n  ✅ No issues detected")
            print("  → System operating normally")
        
        print("\n  Next Steps:")
        print("  → Review full logs: gh run view <id> --log")
        print("  → Check GitHub Actions: https://github.com/YOUR_REPO/actions")
        print("  → Daily monitoring recommended")
    
    def print_quick_commands(self):
        """Print useful quick commands"""
        print("\n" + "=" * 75)
        print("🔧 QUICK COMMANDS")
        print("=" * 75)
        
        commands = [
            ("gh run list", "List recent runs"),
            ("gh run view <id>", "View specific run details"),
            ("gh run view <id> --log", "View run logs"),
            ("gh workflow list", "List all workflows"),
            ("gh run rerun <id>", "Re-run a failed workflow"),
            ("python monitor_pipeline.py", "Run this monitoring script"),
        ]
        
        for cmd, desc in commands:
            print(f"  {cmd:<35} → {desc}")
    
    def generate_report(self):
        """Generate complete monitoring report"""
        self.print_status_header()
        
        runs = self.get_recent_runs()
        self.print_pipeline_health(runs)
        
        metrics = self.get_model_metrics()
        self.print_model_performance(metrics)
        
        data_info = self.check_data_freshness()
        self.print_data_quality(data_info)
        
        self.print_resource_usage()
        self.print_performance_trend()
        
        self.print_summary(runs)
        self.print_quick_commands()
        
        print("\n" + "=" * 75)
        print(f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 75 + "\n")


def main():
    """Main entry point"""
    monitor = PipelineMonitor()
    
    try:
        monitor.generate_report()
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
