import requests
import os

# Set API key
api_key = "788ba39a8f576197768e2c055f49c342"
os.environ['TMDB_API_KEY'] = api_key

# Path to test CSV
csv_path = r"C:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT\test_batch_movies.csv"

# Test endpoint
url = "http://127.0.0.1:8000/predict/batch"

print(f"Testing batch endpoint at {url}")
print(f"CSV file: {csv_path}")
print(f"API Key set: {bool(os.getenv('TMDB_API_KEY'))}")

try:
    with open(csv_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{response.text[:500]}")  # Print first 500 chars
    
    if response.status_code == 200:
        print(f"\n✓ Success! Full response:")
        import json
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n✗ Error response received")
        
except Exception as e:
    print(f"✗ Request failed: {e}")
