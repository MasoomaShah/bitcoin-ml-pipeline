"""
Quick test script to run the Prefect ML pipeline locally.

Usage:
    python test_prefect_pipeline.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "prefect" / "flows"))

# Import the pipeline
from ml_pipeline import ml_training_pipeline

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  PREFECT ML PIPELINE TEST")
    print("="*70 + "\n")
    
    print("This will run the complete ML pipeline:")
    print("  1. Data Ingestion")
    print("  2. Feature Engineering")
    print("  3. Model Training (Regression + Classification)")
    print("  4. Model Evaluation")
    print("  5. Model Versioning & Saving")
    print("  6. Notifications (if webhook configured)")
    print()
    
    # Check if data file exists
    data_path = project_root / "data" / "raw" / "bitcoin_timeseries.csv"
    if not data_path.exists():
        print(f"⚠️  Warning: Data file not found at {data_path}")
        print("   Fetching data from CoinGecko API instead...")
        print()
        fetch_live = True
    else:
        fetch_live = False
    
    # Run the pipeline
    # Note: Using test_days=30 (last 30 days for testing)
    # With 365 total samples, this gives ~333 train / 30 test split (more training data)
    try:
        result = ml_training_pipeline(
            data_path=str(data_path),
            test_days=30,
            output_dir="models",
            notification_type="discord",  # Change to "slack" or "email" as needed
            fetch_live_data=fetch_live  # Fetch from API if CSV not found
        )
        
        print("\n" + "="*70)
        print("  ✅ PIPELINE TEST COMPLETED")
        print("="*70)
        print(f"\nVersion: {result['version']}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
        print(f"\nRegression RMSE: {result['regression_metrics']['rmse']:.4f}")
        print(f"Regression R²: {result['regression_metrics']['r2']:.4f}")
        print(f"\nClassification Accuracy: {result['classification_metrics']['accuracy']:.4f}")
        print(f"Classification F1: {result['classification_metrics']['f1_score']:.4f}")
        print(f"\nModels saved to: models/")
        print()
        
    except Exception as e:
        print("\n" + "="*70)
        print("  ❌ PIPELINE TEST FAILED")
        print("="*70)
        print(f"\nError: {str(e)}")
        print("\nCheck the error messages above for details.")
        print()
        raise
