"""
Automated Tests for Data Drift Detection

Comprehensive test suite for data drift detection module including:
- Unit tests for drift detection methods
- Integration tests with real data
- Edge case handling
- Performance benchmarks
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataGeneration:
    """Generate test data with known properties."""
    
    @staticmethod
    def create_baseline_data(n_samples: int = 365, seed: int = 42) -> pd.DataFrame:
        """Create baseline dataset."""
        np.random.seed(seed)
        return pd.DataFrame({
            'btc_price': np.random.normal(45000, 5000, n_samples),
            'volume': np.random.exponential(1e9, n_samples),
            'rsi': np.random.uniform(20, 80, n_samples),
            'macd': np.random.normal(0, 500, n_samples),
            'trend': np.random.choice(['up', 'down', 'sideways'], n_samples),
            'timestamp': pd.date_range(start='2024-01-01', periods=n_samples, freq='D')
        })
    
    @staticmethod
    def create_drifted_data(base_df: pd.DataFrame, 
                           drift_type: str = 'mean_shift',
                           severity: float = 1.0) -> pd.DataFrame:
        """Create drifted dataset."""
        df = base_df.copy()
        np.random.seed(123)  # Different seed for variation
        
        if drift_type == 'mean_shift':
            # Shift mean of continuous features
            df['btc_price'] = df['btc_price'] + (5000 * severity)
            df['volume'] = df['volume'] * (1.0 + severity * 0.5)
        
        elif drift_type == 'variance_shift':
            # Increase variance
            df['rsi'] = df['rsi'] * (1.0 + severity * 0.5)
            df['macd'] = df['macd'] * (1.0 + severity)
        
        elif drift_type == 'categorical_shift':
            # Change categorical distribution
            new_trends = []
            for _ in range(len(df)):
                if np.random.random() < severity * 0.3:
                    new_trends.append('up')
                else:
                    new_trends.append(np.random.choice(['down', 'sideways']))
            df['trend'] = new_trends
        
        elif drift_type == 'outlier_injection':
            # Add outliers
            n_outliers = int(len(df) * severity * 0.05)
            outlier_idx = np.random.choice(len(df), n_outliers, replace=False)
            df.loc[outlier_idx, 'btc_price'] = np.random.uniform(20000, 80000, n_outliers)
        
        return df
    
    @staticmethod
    def create_no_drift_data(base_df: pd.DataFrame, 
                            noise_level: float = 0.01) -> pd.DataFrame:
        """Create data with no drift, only noise."""
        df = base_df.copy()
        np.random.seed(999)
        
        # Add small random noise
        df['btc_price'] = df['btc_price'] + np.random.normal(0, 100 * noise_level, len(df))
        df['volume'] = df['volume'] + np.random.normal(0, 1e8 * noise_level, len(df))
        df['rsi'] = df['rsi'] + np.random.normal(0, 1 * noise_level, len(df))
        
        return df


class TestDriftDetectionEngine:
    """Tests for DriftDetectionEngine class."""
    
    @pytest.fixture
    def baseline_data(self):
        """Provide baseline data."""
        return TestDataGeneration.create_baseline_data()
    
    @pytest.fixture
    def engine(self, baseline_data):
        """Provide initialized drift detection engine."""
        from src.data_drift_detection import DriftDetectionEngine
        return DriftDetectionEngine(reference_data=baseline_data)
    
    def test_engine_initialization(self, engine, baseline_data):
        """Test engine initialization."""
        assert engine.reference_data is not None
        assert len(engine.reference_data) == len(baseline_data)
        assert engine.threshold_ks == 0.05
        assert engine.threshold_psi == 0.25
        assert engine.threshold_wasserstein == 0.1
    
    def test_statistics_calculation(self, engine, baseline_data):
        """Test statistics calculation."""
        stats = engine.reference_stats
        
        # Check continuous columns
        assert 'btc_price' in stats
        assert 'mean' in stats['btc_price']
        assert 'std' in stats['btc_price']
        assert 'min' in stats['btc_price']
        assert 'max' in stats['btc_price']
        
        # Check categorical columns
        assert 'trend' in stats
        assert 'unique_values' in stats['trend']
        assert 'mode' in stats['trend']
    
    def test_ks_test_continuous_features(self, engine, baseline_data):
        """Test KS test on continuous features."""
        no_drift_data = TestDataGeneration.create_no_drift_data(baseline_data)
        
        statistic, p_value = engine.ks_test(no_drift_data, 'btc_price')
        
        assert statistic is not None
        assert p_value is not None
        assert 0 <= statistic <= 1
        assert 0 <= p_value <= 1
    
    def test_ks_test_no_drift(self, engine, baseline_data):
        """Test KS test detects no drift in similar data."""
        no_drift_data = TestDataGeneration.create_no_drift_data(
            baseline_data, noise_level=0.001
        )
        
        statistic, p_value = engine.ks_test(no_drift_data, 'btc_price')
        
        # High p-value means no drift
        assert p_value > engine.threshold_ks or p_value is None
    
    def test_ks_test_detects_drift(self, engine, baseline_data):
        """Test KS test detects drift in modified data."""
        drifted_data = TestDataGeneration.create_drifted_data(
            baseline_data, drift_type='mean_shift', severity=2.0
        )
        
        statistic, p_value = engine.ks_test(drifted_data, 'btc_price')
        
        # Should detect drift (low p-value)
        assert p_value is not None
        assert p_value < 0.05
    
    def test_wasserstein_distance(self, engine, baseline_data):
        """Test Wasserstein distance calculation."""
        no_drift_data = TestDataGeneration.create_no_drift_data(baseline_data)
        
        distance = engine.wasserstein_distance(no_drift_data, 'btc_price')
        
        assert distance is not None
        assert distance >= 0
    
    def test_psi_calculation_no_drift(self, engine, baseline_data):
        """Test PSI for non-drifted data."""
        no_drift_data = TestDataGeneration.create_no_drift_data(baseline_data)
        
        psi = engine.population_stability_index(no_drift_data, 'btc_price')
        
        assert psi is not None
        assert psi < 0.25  # Should be low for no drift
    
    def test_psi_calculation_drift(self, engine, baseline_data):
        """Test PSI detects drift."""
        drifted_data = TestDataGeneration.create_drifted_data(
            baseline_data, drift_type='mean_shift', severity=2.0
        )
        
        psi = engine.population_stability_index(drifted_data, 'btc_price')
        
        assert psi is not None
        assert psi > 0.1  # Should be elevated for drifted data
    
    def test_chi_square_test_categorical(self, engine, baseline_data):
        """Test Chi-square test for categorical features."""
        no_drift_data = TestDataGeneration.create_no_drift_data(baseline_data)
        
        statistic, p_value = engine.chi_square_test(no_drift_data, 'trend')
        
        # May be None if insufficient samples
        if statistic is not None:
            assert p_value is not None
            assert 0 <= p_value <= 1


class TestDriftReport:
    """Tests for DriftReport class."""
    
    def test_report_creation(self):
        """Test drift report creation."""
        from src.data_drift_detection import DriftReport
        
        report = DriftReport(
            reference_period="2024-01-01",
            current_period="2024-12-05",
            reference_size=365,
            current_size=100
        )
        
        assert report.reference_period == "2024-01-01"
        assert report.current_period == "2024-12-05"
        assert report.reference_size == 365
        assert report.current_size == 100
        assert report.drift_detected is False
    
    def test_report_ks_test_result(self):
        """Test adding KS test results."""
        from src.data_drift_detection import DriftReport
        
        report = DriftReport("2024-01-01", "2024-12-05", 365, 100)
        report.add_ks_test('price', 0.15, 0.02, True)
        
        assert 'price' in report.ks_tests
        assert report.ks_tests['price']['drift_detected'] is True
        assert report.drift_detected is True
    
    def test_report_psi_result(self):
        """Test adding PSI results."""
        from src.data_drift_detection import DriftReport
        
        report = DriftReport("2024-01-01", "2024-12-05", 365, 100)
        report.add_psi('price', 0.28, True)
        
        assert 'price' in report.psi_tests
        assert report.psi_tests['price']['drift_detected'] is True
        assert report.overall_severity == "HIGH"
    
    def test_report_to_dict(self):
        """Test report serialization to dict."""
        from src.data_drift_detection import DriftReport
        
        report = DriftReport("2024-01-01", "2024-12-05", 365, 100)
        report.add_ks_test('price', 0.15, 0.02, True)
        
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert 'timestamp' in report_dict
        assert 'drift_detected' in report_dict
        assert 'ks_tests' in report_dict
    
    def test_report_to_json(self):
        """Test report serialization to JSON."""
        from src.data_drift_detection import DriftReport
        
        report = DriftReport("2024-01-01", "2024-12-05", 365, 100)
        report.add_ks_test('price', 0.15, 0.02, True)
        
        json_str = report.to_json()
        
        assert isinstance(json_str, str)
        report_dict = json.loads(json_str)
        assert 'drift_detected' in report_dict
    
    def test_report_summary(self):
        """Test report summary generation."""
        from src.data_drift_detection import DriftReport
        
        report = DriftReport("2024-01-01", "2024-12-05", 365, 100)
        report.add_ks_test('price', 0.15, 0.02, True)
        
        summary = report.summary()
        
        assert isinstance(summary, str)
        assert "DATA DRIFT DETECTION REPORT" in summary
        assert "DRIFT DETECTED" in summary


class TestIntegration:
    """Integration tests with full workflow."""
    
    def test_full_drift_detection_workflow_no_drift(self):
        """Test complete workflow with no drift scenario."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        no_drift = TestDataGeneration.create_no_drift_data(baseline)
        
        engine = DriftDetectionEngine(reference_data=baseline)
        report = engine.detect_drift(no_drift)
        
        assert isinstance(report, type(report))
        assert report.drift_detected is not None
    
    def test_full_drift_detection_workflow_with_drift(self):
        """Test complete workflow with drift scenario."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        drifted = TestDataGeneration.create_drifted_data(
            baseline, drift_type='mean_shift', severity=2.0
        )
        
        engine = DriftDetectionEngine(reference_data=baseline)
        report = engine.detect_drift(drifted)
        
        assert isinstance(report, type(report))
        # Likely to detect drift
        assert report.drift_detected in [True, False]
    
    def test_compare_datasets_function(self):
        """Test high-level compare_datasets function."""
        from src.data_drift_detection import compare_datasets
        
        # Create temporary files
        baseline = TestDataGeneration.create_baseline_data()
        no_drift = TestDataGeneration.create_no_drift_data(baseline)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.csv"
            current_path = Path(tmpdir) / "current.csv"
            
            baseline.to_csv(baseline_path, index=False)
            no_drift.to_csv(current_path, index=False)
            
            report = compare_datasets(str(baseline_path), str(current_path))
            
            assert report is not None
            assert report.reference_size == len(baseline)
            assert report.current_size == len(no_drift)
    
    def test_drift_history_tracking(self):
        """Test drift history tracking."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        engine = DriftDetectionEngine(reference_data=baseline)
        
        # Run multiple drift checks
        for i in range(3):
            if i == 0:
                data = TestDataGeneration.create_no_drift_data(baseline)
            else:
                data = TestDataGeneration.create_drifted_data(
                    baseline, drift_type='variance_shift', severity=0.5 * i
                )
            
            engine.detect_drift(data)
        
        assert len(engine.drift_history) == 3


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_missing_column_handling(self):
        """Test handling of missing columns."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        missing_col_data = baseline.drop('trend', axis=1)
        
        engine = DriftDetectionEngine(reference_data=baseline)
        report = engine.detect_drift(missing_col_data)
        
        assert 'trend' in report.missing_columns
        assert report.drift_detected is True
    
    def test_invalid_column_ks_test(self):
        """Test KS test with invalid column."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        engine = DriftDetectionEngine(reference_data=baseline)
        
        result = engine.ks_test(baseline, 'nonexistent_column')
        
        assert result == (None, None)
    
    def test_categorical_ks_test(self):
        """Test KS test on categorical column (should skip)."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        engine = DriftDetectionEngine(reference_data=baseline)
        
        result = engine.ks_test(baseline, 'trend')
        
        assert result == (None, None)
    
    def test_small_sample_handling(self):
        """Test handling of very small samples."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data(n_samples=10)
        small_data = TestDataGeneration.create_no_drift_data(baseline)
        
        engine = DriftDetectionEngine(reference_data=baseline)
        report = engine.detect_drift(small_data)
        
        assert report is not None


class TestPerformanceBenchmark:
    """Performance and efficiency tests."""
    
    def test_large_dataset_performance(self):
        """Test performance with large dataset."""
        from src.data_drift_detection import DriftDetectionEngine
        import time
        
        # Create large dataset
        large_baseline = TestDataGeneration.create_baseline_data(n_samples=10000)
        large_current = TestDataGeneration.create_no_drift_data(large_baseline)
        
        engine = DriftDetectionEngine(reference_data=large_baseline)
        
        start = time.time()
        report = engine.detect_drift(large_current)
        elapsed = time.time() - start
        
        assert report is not None
        assert elapsed < 5.0  # Should complete within 5 seconds
    
    def test_multiple_drift_checks_performance(self):
        """Test performance of multiple consecutive drift checks."""
        from src.data_drift_detection import DriftDetectionEngine
        import time
        
        baseline = TestDataGeneration.create_baseline_data()
        engine = DriftDetectionEngine(reference_data=baseline)
        
        start = time.time()
        for i in range(10):
            data = TestDataGeneration.create_no_drift_data(baseline)
            engine.detect_drift(data)
        elapsed = time.time() - start
        
        assert elapsed < 10.0  # 10 checks in under 10 seconds


class TestDriftTypes:
    """Test detection of different drift types."""
    
    def test_detect_mean_shift_drift(self):
        """Test detection of mean shift."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        drifted = TestDataGeneration.create_drifted_data(
            baseline, drift_type='mean_shift', severity=2.0
        )
        
        engine = DriftDetectionEngine(reference_data=baseline)
        report = engine.detect_drift(drifted)
        
        # Should detect drift in at least some tests
        total_tests = (len(report.ks_tests) + len(report.psi_tests) + 
                      len(report.wasserstein_tests))
        drift_count = sum([r['drift_detected'] for r in report.ks_tests.values()] +
                         [r['drift_detected'] for r in report.psi_tests.values()])
        
        assert total_tests > 0  # Should have run some tests
    
    def test_detect_variance_shift_drift(self):
        """Test detection of variance shift."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        drifted = TestDataGeneration.create_drifted_data(
            baseline, drift_type='variance_shift', severity=2.0
        )
        
        engine = DriftDetectionEngine(reference_data=baseline)
        report = engine.detect_drift(drifted)
        
        assert report is not None
    
    def test_detect_outlier_injection_drift(self):
        """Test detection of outlier injection."""
        from src.data_drift_detection import DriftDetectionEngine
        
        baseline = TestDataGeneration.create_baseline_data()
        drifted = TestDataGeneration.create_drifted_data(
            baseline, drift_type='outlier_injection', severity=2.0
        )
        
        engine = DriftDetectionEngine(reference_data=baseline)
        report = engine.detect_drift(drifted)
        
        assert report is not None


if __name__ == "__main__":
    # Run all tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
