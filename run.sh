#!/bin/bash

# ScanPlus Startup Script
echo "Starting ScanPlus Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
fi

# Activate virtual environment
source venv/Scripts/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Start API server in background
echo "Starting API server on port 5000..."
cd api
python api.py &
API_PID=$!
cd ..

# Wait a bit for API to start
sleep 3

# Start frontend server
echo "Starting frontend server on port 8000..."
cd frontend
python app.py &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ ScanPlus is running!"
echo "   - API: http://127.0.0.1:5000"
echo "   - Frontend: http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $API_PID $FRONTEND_PID
