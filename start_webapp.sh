#!/bin/bash
# Bitcoin ML Web App Launcher for Linux/Mac

echo "🚀 Starting Bitcoin ML Web App..."
echo ""

# Check if models exist
if [ ! -f "models/manifest.json" ]; then
    echo "⚠️  No trained models found!"
    echo "   Please train models first:"
    echo "   python src/train_with_feature_store.py"
    echo ""
    read -p "Would you like to train models now? (y/n) " train
    if [ "$train" = "y" ]; then
        python src/train_with_feature_store.py
        echo ""
    else
        exit 1
    fi
fi

echo "✓ Models found"
echo ""

# Ask which component to run
echo "Select what to run:"
echo "1. Streamlit Dashboard only (recommended)"
echo "2. FastAPI Server only"
echo "3. Both Dashboard and API Server"
echo ""

read -p "Enter choice (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "🎨 Starting Streamlit Dashboard..."
        echo "   Opening at http://localhost:8501"
        echo ""
        streamlit run app.py
        ;;
    2)
        echo ""
        echo "⚡ Starting FastAPI Server..."
        echo "   API: http://localhost:8000"
        echo "   Docs: http://localhost:8000/docs"
        echo ""
        python api_server.py
        ;;
    3)
        echo ""
        echo "🚀 Starting both components..."
        echo ""
        echo "   Dashboard: http://localhost:8501"
        echo "   API: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo ""
        
        # Start API server in background
        python api_server.py &
        API_PID=$!
        
        # Wait for API to start
        sleep 2
        
        # Start Streamlit dashboard
        streamlit run app.py
        
        # Kill API server when Streamlit exits
        kill $API_PID 2>/dev/null
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
