#!/usr/bin/env python3
"""
Alert Management System for CI/CD Pipeline
Monitors thresholds and sends notifications
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import subprocess


class AlertConfig:
    """Configuration for alert thresholds"""
    
    # Pipeline thresholds
    PIPELINE_SUCCESS_RATE_WARNING = 90  # %
    PIPELINE_SUCCESS_RATE_CRITICAL = 80  # %
    MAX_BUILD_TIME = 30  # minutes
    
    # Model thresholds
    MODEL_ACCURACY_WARNING = 0.65  # 65%
    MODEL_F1_WARNING = 0.65
    
    # Data thresholds
    MAX_DATA_AGE = 24  # hours
    
    # Artifact thresholds
    MAX_ARTIFACT_SIZE = 1000  # MB


class Alert:
    """Represents a single alert"""
    
    LEVELS = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'critical': '🔴'
    }
    
    def __init__(self, level: str, title: str, message: str, action: str = None):
        self.level = level
        self.title = title
        self.message = message
        self.action = action
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        """Convert alert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'level': self.level,
            'title': self.title,
            'message': self.message,
            'action': self.action
        }
    
    def to_string(self) -> str:
        """Format alert as string"""
        emoji = self.LEVELS.get(self.level, '•')
        text = f"{emoji} [{self.level.upper()}] {self.title}\n"
        text += f"   {self.message}\n"
        if self.action:
            text += f"   → {self.action}"
        return text
    
    def to_discord(self) -> dict:
        """Format alert for Discord webhook"""
        color_map = {
            'info': 0x3498db,      # Blue
            'warning': 0xf39c12,   # Orange
            'critical': 0xe74c3c   # Red
        }
        
        return {
            'embeds': [{
                'title': self.title,
                'description': self.message,
                'color': color_map.get(self.level, 0x3498db),
                'fields': [
                    {
                        'name': 'Level',
                        'value': self.level.upper(),
                        'inline': True
                    },
                    {
                        'name': 'Timestamp',
                        'value': self.timestamp,
                        'inline': True
                    }
                ],
                'footer': {
                    'text': 'CI/CD Pipeline Monitor'
                }
            }]
        }


class AlertManager:
    """Manage alerts and thresholds"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.config = AlertConfig()
        self.alert_log = 'alerts.jsonl'
    
    def check_pipeline_success_rate(self, success_rate: float) -> Optional[Alert]:
        """Check if pipeline success rate is acceptable"""
        if success_rate < self.config.PIPELINE_SUCCESS_RATE_CRITICAL:
            return Alert(
                'critical',
                'Pipeline Critical Failure',
                f'Success rate {success_rate:.1f}% below critical threshold ({self.config.PIPELINE_SUCCESS_RATE_CRITICAL}%)',
                'Review failed runs immediately'
            )
        elif success_rate < self.config.PIPELINE_SUCCESS_RATE_WARNING:
            return Alert(
                'warning',
                'Pipeline Performance Degradation',
                f'Success rate {success_rate:.1f}% below warning threshold ({self.config.PIPELINE_SUCCESS_RATE_WARNING}%)',
                'Review recent run logs'
            )
        return None
    
    def check_model_accuracy(self, accuracy: float) -> Optional[Alert]:
        """Check if model accuracy is acceptable"""
        if accuracy < self.config.MODEL_ACCURACY_WARNING:
            return Alert(
                'warning',
                'Model Accuracy Below Threshold',
                f'Model accuracy {accuracy:.4f} below threshold ({self.config.MODEL_ACCURACY_WARNING})',
                'Review training data or retrain model'
            )
        return None
    
    def check_data_freshness(self, age_hours: float) -> Optional[Alert]:
        """Check if data is fresh enough"""
        if age_hours > self.config.MAX_DATA_AGE:
            return Alert(
                'warning',
                'Data Staleness Warning',
                f'Data is {age_hours:.1f} hours old (max: {self.config.MAX_DATA_AGE} hours)',
                'Check data source and API connection'
            )
        return None
    
    def check_build_time(self, build_time_minutes: float) -> Optional[Alert]:
        """Check if build time is acceptable"""
        if build_time_minutes > self.config.MAX_BUILD_TIME:
            return Alert(
                'info',
                'Build Time Exceeds Target',
                f'Build took {build_time_minutes:.1f} minutes (target: {self.config.MAX_BUILD_TIME} min)',
                'Consider optimizing workflows or caching'
            )
        return None
    
    def check_performance_degradation(self, trend: dict) -> Optional[Alert]:
        """Check for performance degradation"""
        if trend and trend.get('change_percent', 0) < -5:
            return Alert(
                'warning',
                'Model Performance Degradation',
                f'Accuracy declined by {abs(trend["change_percent"]):.2f}% over recent runs',
                'Review training data and model configuration'
            )
        return None
    
    def add_alert(self, alert: Alert):
        """Add alert to list"""
        self.alerts.append(alert)
        self.log_alert(alert)
    
    def log_alert(self, alert: Alert):
        """Log alert to file"""
        try:
            with open(self.alert_log, 'a') as f:
                f.write(json.dumps(alert.to_dict()) + '\n')
        except Exception as e:
            print(f"Error logging alert: {e}")
    
    def send_discord_notification(self, alerts: List[Alert]):
        """Send alerts to Discord"""
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        
        if not webhook_url:
            print("ℹ️  Discord webhook not configured")
            return
        
        try:
            import requests
            
            for alert in alerts:
                requests.post(
                    webhook_url,
                    json=alert.to_discord(),
                    timeout=10
                )
        except ImportError:
            print("⚠️  requests library not installed")
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
    
    def print_alerts(self):
        """Print all alerts"""
        if not self.alerts:
            print("✅ No alerts")
            return
        
        print(f"\n🚨 ALERTS ({len(self.alerts)})")
        print("-" * 70)
        for alert in self.alerts:
            print(alert.to_string())
    
    def get_alert_summary(self) -> dict:
        """Get summary of alerts by level"""
        summary = {
            'critical': 0,
            'warning': 0,
            'info': 0,
            'total': len(self.alerts)
        }
        
        for alert in self.alerts:
            summary[alert.level] += 1
        
        return summary


class HealthCheck:
    """Comprehensive health check"""
    
    def __init__(self):
        self.alert_manager = AlertManager()
    
    def run_checks(self, metrics: dict, runs: list, data_info: dict) -> List[Alert]:
        """Run all health checks"""
        alerts = []
        
        # Calculate success rate
        if runs:
            successful = sum(1 for r in runs if r.get('conclusion') == 'success')
            success_rate = (successful / len(runs)) * 100
            
            alert = self.alert_manager.check_pipeline_success_rate(success_rate)
            if alert:
                alerts.append(alert)
        
        # Check model metrics
        if metrics:
            alert = self.alert_manager.check_model_accuracy(metrics.get('accuracy', 1))
            if alert:
                alerts.append(alert)
        
        # Check data freshness
        if data_info and 'age_hours' in data_info:
            alert = self.alert_manager.check_data_freshness(data_info['age_hours'])
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def generate_health_report(self, metrics: dict, runs: list, data_info: dict) -> str:
        """Generate health report"""
        alerts = self.run_checks(metrics, runs, data_info)
        
        summary = self.alert_manager.alert_manager.get_alert_summary() if hasattr(
            self.alert_manager, 'alert_manager'
        ) else AlertManager().get_alert_summary()
        
        # Update alerts in manager
        self.alert_manager.alerts = alerts
        
        report = f"\n{'='*70}\n"
        report += "🏥 SYSTEM HEALTH CHECK\n"
        report += f"{'='*70}\n\n"
        
        if not alerts:
            report += "✅ All systems operational\n"
        else:
            report += f"⚠️  {len(alerts)} issue(s) detected\n\n"
            for alert in alerts:
                report += alert.to_string() + "\n\n"
        
        report += f"{'='*70}\n"
        
        return report


# Configuration template
ALERT_CONFIG_TEMPLATE = """
# Alert Configuration

## Pipeline Thresholds
PIPELINE_SUCCESS_RATE_WARNING = 90  # %
PIPELINE_SUCCESS_RATE_CRITICAL = 80  # %
MAX_BUILD_TIME = 30  # minutes

## Model Thresholds
MODEL_ACCURACY_WARNING = 0.65  # 65%
MODEL_F1_WARNING = 0.65

## Data Thresholds
MAX_DATA_AGE = 24  # hours

## Artifact Thresholds
MAX_ARTIFACT_SIZE = 1000  # MB

## Notification Channels
DISCORD_WEBHOOK_URL = ${DISCORD_WEBHOOK_URL}
SLACK_WEBHOOK_URL = ${SLACK_WEBHOOK_URL}
EMAIL_RECIPIENTS = ["your-email@gmail.com"]
"""


if __name__ == '__main__':
    # Example usage
    checker = HealthCheck()
    
    # Mock data for testing
    test_metrics = {
        'accuracy': 0.70,
        'f1_score': 0.68,
        'rmse': 1.2
    }
    
    test_runs = [
        {'conclusion': 'success'} for _ in range(28)
    ] + [
        {'conclusion': 'failure'} for _ in range(2)
    ]
    
    test_data = {
        'age_hours': 5,
        'fresh': True
    }
    
    report = checker.generate_health_report(test_metrics, test_runs, test_data)
    print(report)
