"""Check if API routes are properly registered"""

try:
    import api_server
    print("API module loaded successfully")
    
    app = api_server.app
    print(f"FastAPI app created: {app}")
    
    # List all routes
    print("\nRegistered routes:")
    for route in app.routes:
        print(f"  {route.path} - {route.methods}")
    
    # Check if /explain route exists
    explain_routes = [r for r in app.routes if '/explain' in r.path]
    if explain_routes:
        print(f"\n[OK] Found {len(explain_routes)} /explain routes:")
        for route in explain_routes:
            print(f"    {route.path} - {route.methods}")
    else:
        print(f"\n[ERROR] No /explain routes found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
