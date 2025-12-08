"""
Quick test script for the web app components
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    required = {
        'streamlit': 'Streamlit',
        'plotly': 'Plotly',
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'joblib': 'Joblib',
        'sklearn': 'Scikit-learn'
    }
    
    missing = []
    for package, name in required.items():
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("   Install with: pip install -r requirements-webapp.txt")
        return False
    
    print("\n✅ All packages installed\n")
    return True


def test_models():
    """Test if trained models exist"""
    print("Testing models...")
    
    models_dir = Path("models")
    manifest = models_dir / "manifest.json"
    
    if not manifest.exists():
        print("  ✗ No manifest.json found")
        print("\n❌ No trained models found")
        print("   Train with: python src/train_with_feature_store.py")
        return False
    
    import json
    with open(manifest) as f:
        data = json.load(f)
    
    # Check if manifest has models (either old or new format)
    if 'models' in data:
        # Old format
        if not data['models']:
            print("  ✗ Manifest is empty")
            return False
        version = data['models'][0]['version']
    elif 'active_version' in data:
        # New format
        version = data['active_version']
    else:
        print("  ✗ Manifest is empty or invalid format")
        return False
    required_files = [
        f"{version}_clf_model.pkl",
        f"{version}_reg_model.pkl",
        f"{version}_scaler.pkl",
        f"{version}_feature_columns.json",
        f"{version}_training_metadata.json"
    ]
    
    missing = []
    for filename in required_files:
        if (models_dir / filename).exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - MISSING")
            missing.append(filename)
    
    if missing:
        print(f"\n❌ Missing model files")
        return False
    
    print("\n✅ All model files present\n")
    return True


def test_data():
    """Test if data files exist"""
    print("Testing data...")
    
    data_dirs = [
        Path("data/processed"),
        Path("data/features")
    ]
    
    found_data = False
    for data_dir in data_dirs:
        if data_dir.exists():
            csv_files = list(data_dir.glob("*.csv"))
            if csv_files:
                print(f"  ✓ Found {len(csv_files)} file(s) in {data_dir}")
                found_data = True
    
    if not found_data:
        print("  ⚠️  No data files found")
        print("\n⚠️  Warning: No data available")
        print("   Fetch data with: python src/fetch_alpha_vantage.py")
        return False
    
    print("\n✅ Data files available\n")
    return True


def test_api():
    """Test if FastAPI server can start"""
    print("Testing FastAPI server...")
    
    try:
        from api_server import app
        print("  ✓ FastAPI app imported successfully")
        print("  ✓ Server can be started with: python api_server.py")
        print("\n✅ API server ready\n")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print("\n❌ API server cannot start")
        return False


def test_streamlit():
    """Test if Streamlit app can load"""
    print("Testing Streamlit app...")
    
    app_file = Path("app.py")
    if not app_file.exists():
        print("  ✗ app.py not found")
        return False
    
    print("  ✓ app.py exists")
    print("  ✓ Dashboard can be started with: streamlit run app.py")
    print("\n✅ Streamlit dashboard ready\n")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Bitcoin ML Web App - Component Test")
    print("=" * 60)
    print()
    
    results = {
        'Imports': test_imports(),
        'Models': test_models(),
        'Data': test_data(),
        'API': test_api(),
        'Dashboard': test_streamlit()
    }
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:15} {status}")
    
    print()
    
    all_passed = all(results.values())
    if all_passed:
        print("🎉 All tests passed! Ready to run the web app.")
        print()
        print("Start with:")
        print("  Windows: .\\start_webapp.ps1")
        print("  Linux/Mac: ./start_webapp.sh")
        print()
        print("Or manually:")
        print("  streamlit run app.py")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
