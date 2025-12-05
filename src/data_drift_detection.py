"""
Data Drift Detection Module

Monitors for statistical changes in data distribution over time.
Detects concept drift, data shift, and feature drift using multiple statistical tests.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import wasserstein_distance
from scipy.stats import ks_2samp, chi2_contingency

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriftDetectionEngine:
    """
    Statistical drift detection engine using multiple test methods.
    
    Supported drift detection methods:
    - Kolmogorov-Smirnov (KS) test for continuous features
    - Chi-square test for categorical features
    - Wasserstein distance for distribution comparison
    - Population Stability Index (PSI)
    """
    
    def __init__(self, 
                 reference_data: pd.DataFrame,
                 threshold_ks: float = 0.05,
                 threshold_psi: float = 0.25,
                 threshold_wasserstein: float = 0.1,
                 reference_period: str = "2024-12-01"):
        """
        Initialize drift detection engine.
        
        Args:
            reference_data: Baseline data for drift comparison
            threshold_ks: KS test p-value threshold (default 0.05)
            threshold_psi: PSI threshold (default 0.25)
            threshold_wasserstein: Wasserstein distance threshold (default 0.1)
            reference_period: Label for reference period
        """
        self.reference_data = reference_data
        self.threshold_ks = threshold_ks
        self.threshold_psi = threshold_psi
        self.threshold_wasserstein = threshold_wasserstein
        self.reference_period = reference_period
        
        # Store reference statistics
        self.reference_stats = self._calculate_statistics(reference_data)
        self.drift_history = []
        
        logger.info(f"Drift detection engine initialized with {len(reference_data)} baseline records")
    
    def _calculate_statistics(self, data: pd.DataFrame) -> Dict:
        """Calculate statistical measures for a dataset."""
        stats_dict = {}
        
        for col in data.columns:
            if data[col].dtype in ['float64', 'int64']:
                stats_dict[col] = {
                    'mean': data[col].mean(),
                    'std': data[col].std(),
                    'min': data[col].min(),
                    'max': data[col].max(),
                    'median': data[col].median(),
                    'q25': data[col].quantile(0.25),
                    'q75': data[col].quantile(0.75),
                    'distribution': data[col].values
                }
            else:
                stats_dict[col] = {
                    'unique_values': data[col].nunique(),
                    'mode': data[col].mode()[0] if len(data[col].mode()) > 0 else None,
                    'distribution': data[col].value_counts().to_dict()
                }
        
        return stats_dict
    
    def ks_test(self, current_data: pd.DataFrame, column: str) -> Tuple[float, float]:
        """
        Kolmogorov-Smirnov test for continuous variables.
        
        Returns:
            (statistic, p_value)
        """
        if column not in self.reference_data.columns:
            return None, None
        
        if self.reference_data[column].dtype not in ['float64', 'int64']:
            return None, None
        
        reference_dist = self.reference_stats[column]['distribution']
        current_dist = current_data[column].values
        
        statistic, p_value = ks_2samp(reference_dist, current_dist)
        return statistic, p_value
    
    def wasserstein_distance(self, current_data: pd.DataFrame, column: str) -> float:
        """
        Wasserstein distance (Earth Mover's Distance) between distributions.
        
        Returns:
            Distance value (lower = more similar)
        """
        if column not in self.reference_data.columns:
            return None
        
        if self.reference_data[column].dtype not in ['float64', 'int64']:
            return None
        
        reference_dist = self.reference_stats[column]['distribution']
        current_dist = current_data[column].values
        
        # Normalize to same length for comparison
        min_len = min(len(reference_dist), len(current_dist))
        reference_sample = np.random.choice(reference_dist, min_len, replace=False)
        current_sample = np.random.choice(current_dist, min_len, replace=False)
        
        distance = wasserstein_distance(reference_sample, current_sample)
        return distance
    
    def population_stability_index(self, current_data: pd.DataFrame, column: str) -> float:
        """
        Population Stability Index (PSI) - measures shift in distribution.
        
        PSI < 0.10 = No significant population change
        PSI 0.10-0.25 = Small population change
        PSI > 0.25 = Significant population change (drift detected)
        
        Returns:
            PSI value
        """
        if column not in self.reference_data.columns:
            return None
        
        if self.reference_data[column].dtype not in ['float64', 'int64']:
            return None
        
        reference = self.reference_stats[column]['distribution']
        current = current_data[column].values
        
        # Create bins
        bins = np.histogram_bin_edges(np.concatenate([reference, current]), bins=10)
        
        # Calculate frequencies
        ref_counts = np.histogram(reference, bins=bins)[0]
        curr_counts = np.histogram(current, bins=bins)[0]
        
        # Normalize
        ref_pct = ref_counts / len(reference)
        curr_pct = curr_counts / len(current)
        
        # Calculate PSI
        psi = np.sum((curr_pct - ref_pct) * np.log((curr_pct + 1e-10) / (ref_pct + 1e-10)))
        
        return psi
    
    def chi_square_test(self, current_data: pd.DataFrame, column: str) -> Tuple[float, float]:
        """
        Chi-square test for categorical variables.
        
        Returns:
            (statistic, p_value)
        """
        if column not in self.reference_data.columns:
            return None, None
        
        if self.reference_data[column].dtype not in ['object', 'category']:
            return None, None
        
        # Create contingency table
        ref_counts = self.reference_data[column].value_counts()
        curr_counts = current_data[column].value_counts()
        
        # Align indices
        all_categories = set(ref_counts.index) | set(curr_counts.index)
        ref_counts = ref_counts.reindex(all_categories, fill_value=0)
        curr_counts = curr_counts.reindex(all_categories, fill_value=0)
        
        contingency = np.array([ref_counts.values, curr_counts.values])
        
        try:
            chi2, p_value, dof, expected = chi2_contingency(contingency)
            return chi2, p_value
        except:
            return None, None
    
    def detect_drift(self, current_data: pd.DataFrame) -> 'DriftReport':
        """
        Perform comprehensive drift detection on current data.
        
        Args:
            current_data: New data to check for drift
            
        Returns:
            DriftReport object with detailed results
        """
        report = DriftReport(
            reference_period=self.reference_period,
            current_period=datetime.now().isoformat(),
            reference_size=len(self.reference_data),
            current_size=len(current_data)
        )
        
        # Test each column
        for col in self.reference_data.columns:
            if col not in current_data.columns:
                report.add_missing_column(col)
                continue
            
            if self.reference_data[col].dtype in ['float64', 'int64']:
                # KS Test
                ks_stat, ks_p = self.ks_test(current_data, col)
                if ks_stat is not None:
                    is_drift_ks = ks_p < self.threshold_ks
                    report.add_ks_test(col, ks_stat, ks_p, is_drift_ks)
                
                # Wasserstein Distance
                ws_dist = self.wasserstein_distance(current_data, col)
                if ws_dist is not None:
                    is_drift_ws = ws_dist > self.threshold_wasserstein
                    report.add_wasserstein(col, ws_dist, is_drift_ws)
                
                # PSI
                psi = self.population_stability_index(current_data, col)
                if psi is not None:
                    is_drift_psi = psi > self.threshold_psi
                    report.add_psi(col, psi, is_drift_psi)
            
            else:
                # Chi-square test
                chi2, p_val = self.chi_square_test(current_data, col)
                if chi2 is not None:
                    is_drift = p_val < self.threshold_ks
                    report.add_chi_square(col, chi2, p_val, is_drift)
        
        # Store in history
        self.drift_history.append(report.to_dict())
        
        return report


class DriftReport:
    """Comprehensive drift detection report."""
    
    def __init__(self, reference_period: str, current_period: str, 
                 reference_size: int, current_size: int):
        self.reference_period = reference_period
        self.current_period = current_period
        self.reference_size = reference_size
        self.current_size = current_size
        self.timestamp = datetime.now()
        
        self.ks_tests = {}
        self.wasserstein_tests = {}
        self.psi_tests = {}
        self.chi_square_tests = {}
        self.missing_columns = []
        self.drift_detected = False
        self.overall_severity = "LOW"
    
    def add_ks_test(self, column: str, statistic: float, p_value: float, drift_detected: bool):
        """Add KS test result."""
        self.ks_tests[column] = {
            'statistic': round(statistic, 6),
            'p_value': round(p_value, 6),
            'drift_detected': drift_detected,
            'interpretation': 'DRIFT' if drift_detected else 'NO_DRIFT'
        }
        if drift_detected:
            self.drift_detected = True
    
    def add_wasserstein(self, column: str, distance: float, drift_detected: bool):
        """Add Wasserstein distance result."""
        self.wasserstein_tests[column] = {
            'distance': round(distance, 6),
            'drift_detected': drift_detected,
            'interpretation': 'DRIFT' if drift_detected else 'NO_DRIFT'
        }
        if drift_detected:
            self.drift_detected = True
    
    def add_psi(self, column: str, psi_value: float, drift_detected: bool):
        """Add PSI result."""
        self.psi_tests[column] = {
            'psi': round(psi_value, 6),
            'drift_detected': drift_detected,
            'interpretation': 'DRIFT' if drift_detected else 'NO_DRIFT',
            'severity': self._get_psi_severity(psi_value)
        }
        if drift_detected:
            self.drift_detected = True
            self.overall_severity = "HIGH"
    
    def add_chi_square(self, column: str, statistic: float, p_value: float, drift_detected: bool):
        """Add Chi-square test result."""
        self.chi_square_tests[column] = {
            'statistic': round(statistic, 6),
            'p_value': round(p_value, 6),
            'drift_detected': drift_detected,
            'interpretation': 'DRIFT' if drift_detected else 'NO_DRIFT'
        }
        if drift_detected:
            self.drift_detected = True
    
    def add_missing_column(self, column: str):
        """Track missing columns."""
        self.missing_columns.append(column)
        self.drift_detected = True
        self.overall_severity = "CRITICAL"
    
    @staticmethod
    def _get_psi_severity(psi: float) -> str:
        """Determine PSI severity level."""
        if psi < 0.10:
            return "LOW"
        elif psi < 0.25:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'reference_period': self.reference_period,
            'current_period': self.current_period,
            'reference_size': self.reference_size,
            'current_size': self.current_size,
            'drift_detected': self.drift_detected,
            'overall_severity': self.overall_severity,
            'ks_tests': self.ks_tests,
            'wasserstein_tests': self.wasserstein_tests,
            'psi_tests': self.psi_tests,
            'chi_square_tests': self.chi_square_tests,
            'missing_columns': self.missing_columns
        }
    
    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 70,
            "DATA DRIFT DETECTION REPORT",
            "=" * 70,
            f"\nReference Period: {self.reference_period} ({self.reference_size} records)",
            f"Current Period:   {self.current_period} ({self.current_size} records)",
            f"Timestamp:        {self.timestamp.isoformat()}",
            f"\nOVERALL VERDICT: {'🚨 DRIFT DETECTED' if self.drift_detected else '✅ NO DRIFT DETECTED'}",
            f"Severity Level:   {self.overall_severity}",
        ]
        
        if self.missing_columns:
            lines.append(f"\n⚠️  Missing Columns ({len(self.missing_columns)}):")
            for col in self.missing_columns:
                lines.append(f"   - {col}")
        
        if self.ks_tests:
            lines.append(f"\n📊 Kolmogorov-Smirnov Tests ({len(self.ks_tests)} features):")
            for col, result in self.ks_tests.items():
                status = "🚨 DRIFT" if result['drift_detected'] else "✅ OK"
                lines.append(f"   {col:20} {status:15} (p={result['p_value']:.6f})")
        
        if self.wasserstein_tests:
            lines.append(f"\n📈 Wasserstein Distance Tests ({len(self.wasserstein_tests)} features):")
            for col, result in self.wasserstein_tests.items():
                status = "🚨 DRIFT" if result['drift_detected'] else "✅ OK"
                lines.append(f"   {col:20} {status:15} (dist={result['distance']:.6f})")
        
        if self.psi_tests:
            lines.append(f"\n📉 Population Stability Index ({len(self.psi_tests)} features):")
            for col, result in self.psi_tests.items():
                status = f"🚨 DRIFT ({result['severity']})" if result['drift_detected'] else "✅ OK"
                lines.append(f"   {col:20} {status:20} (PSI={result['psi']:.6f})")
        
        if self.chi_square_tests:
            lines.append(f"\n🏷️  Chi-Square Tests ({len(self.chi_square_tests)} features):")
            for col, result in self.chi_square_tests.items():
                status = "🚨 DRIFT" if result['drift_detected'] else "✅ OK"
                lines.append(f"   {col:20} {status:15} (p={result['p_value']:.6f})")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


def load_reference_data(filepath: str, period_label: str = None) -> Tuple[pd.DataFrame, str]:
    """Load reference data from CSV."""
    df = pd.read_csv(filepath)
    if period_label is None:
        period_label = f"Reference ({len(df)} records)"
    return df, period_label


def compare_datasets(reference_path: str, current_path: str) -> DriftReport:
    """
    Compare two datasets and generate drift report.
    
    Args:
        reference_path: Path to reference (baseline) data
        current_path: Path to current data to check
        
    Returns:
        DriftReport with comprehensive results
    """
    ref_data, ref_label = load_reference_data(reference_path, "Reference")
    curr_data, _ = load_reference_data(current_path)
    
    engine = DriftDetectionEngine(
        reference_data=ref_data,
        reference_period=ref_label
    )
    
    report = engine.detect_drift(curr_data)
    return report


if __name__ == "__main__":
    # Example usage
    print("Data Drift Detection Module")
    print("=" * 70)
    print("\nThis module provides statistical drift detection using:")
    print("- Kolmogorov-Smirnov (KS) Test")
    print("- Wasserstein Distance")
    print("- Population Stability Index (PSI)")
    print("- Chi-Square Test")
    print("\nUsage:")
    print("  from src.data_drift_detection import DriftDetectionEngine, compare_datasets")
    print("  report = compare_datasets('reference.csv', 'current.csv')")
    print("  print(report.summary())")
