#!/bin/bash
echo "Starting PHIP locally..."

# Function to kill processes on exit
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

# Start Backend
echo "Starting Backend on http://localhost:8000..."
cd backend
# Ensure PYTHONPATH includes backend directory
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting Frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Services are running!"
echo "Backend API Docs: http://localhost:8000/docs"
echo "Frontend Dashboard: http://localhost:5173"
echo "Press Ctrl+C to stop all services."

wait
