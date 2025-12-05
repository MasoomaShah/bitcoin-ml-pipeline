"""
Daily Data Drift Check Script

Runs data drift detection daily and generates reports/alerts.
Integrated with scheduled-training workflow.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create reports directory
REPORTS_DIR = Path('reports/drift_reports')
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_baseline_data(max_records: int = 365) -> pd.DataFrame:
    """Load baseline reference data."""
    try:
        df = pd.read_csv('data/raw/bitcoin_timeseries.csv')
        logger.info(f"Loaded {len(df)} records from bitcoin_timeseries.csv")
        
        # Use most recent records as reference if available
        if len(df) > max_records:
            df = df.iloc[-max_records:]
        
        return df
    except FileNotFoundError:
        logger.error("bitcoin_timeseries.csv not found")
        return None


def load_current_data(days: int = 7) -> pd.DataFrame:
    """Load recent data for drift checking."""
    try:
        df = pd.read_csv('data/raw/bitcoin_timeseries.csv')
        
        # Get most recent data
        if len(df) > days:
            df = df.iloc[-days:]
        
        logger.info(f"Loaded {len(df)} recent records for drift checking")
        return df
    except FileNotFoundError:
        logger.error("bitcoin_timeseries.csv not found")
        return None


def run_drift_detection():
    """Run comprehensive drift detection."""
    from src.data_drift_detection import DriftDetectionEngine
    
    logger.info("=" * 70)
    logger.info("STARTING DATA DRIFT DETECTION")
    logger.info("=" * 70)
    
    # Load data
    baseline = load_baseline_data(max_records=365)
    current = load_current_data(days=7)
    
    if baseline is None or current is None:
        logger.error("Failed to load required data")
        return False
    
    try:
        # Initialize drift detection engine
        engine = DriftDetectionEngine(
            reference_data=baseline,
            threshold_ks=0.05,
            threshold_psi=0.25,
            threshold_wasserstein=0.1,
            reference_period=f"Last 365 days ({len(baseline)} records)"
        )
        logger.info("Drift detection engine initialized")
        
        # Run drift detection
        logger.info("Running drift detection tests...")
        report = engine.detect_drift(current)
        
        # Print summary
        logger.info("\n" + report.summary())
        
        # Save report as JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS_DIR / f"drift_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        logger.info(f"\n✅ Report saved: {report_path}")
        
        # Log drift status
        if report.drift_detected:
            logger.warning(f"🚨 DRIFT DETECTED - Severity: {report.overall_severity}")
            return_status = 1
        else:
            logger.info("✅ No drift detected - data is stable")
            return_status = 0
        
        # Create summary for next steps
        summary = {
            'timestamp': datetime.now().isoformat(),
            'drift_detected': report.drift_detected,
            'severity': report.overall_severity,
            'reference_size': report.reference_size,
            'current_size': report.current_size,
            'tests_run': {
                'ks_tests': len(report.ks_tests),
                'psi_tests': len(report.psi_tests),
                'wasserstein_tests': len(report.wasserstein_tests),
                'chi_square_tests': len(report.chi_square_tests)
            },
            'features_affected': [
                col for col, result in report.psi_tests.items() 
                if result['drift_detected']
            ]
        }
        
        # Save summary
        summary_path = REPORTS_DIR / f"summary_{timestamp}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info("=" * 70)
        logger.info("DRIFT DETECTION COMPLETE")
        logger.info("=" * 70)
        
        return return_status == 0
        
    except Exception as e:
        logger.error(f"Error during drift detection: {e}", exc_info=True)
        return False


def create_alerts(report_dict: dict) -> dict:
    """Create alerts based on drift report."""
    from alert_manager import AlertManager, AlertConfig
    
    alerts = []
    
    if report_dict['drift_detected']:
        alert_level = "CRITICAL" if report_dict['severity'] == "HIGH" else "WARNING"
        
        alerts.append({
            'level': alert_level,
            'message': f"Data drift detected with {report_dict['severity']} severity",
            'features_affected': report_dict.get('features_affected', []),
            'action_required': True
        })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'alerts': alerts,
        'total_alerts': len(alerts)
    }


def main():
    """Main execution."""
    try:
        success = run_drift_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
