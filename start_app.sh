#!/bin/bash
# Start both proxy server and HTTP server for Trading Decision App

echo "Starting Trading Decision App..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing required Python packages..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install required packages"
        echo "Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $PROXY_PID $HTTP_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start proxy server in background
echo "Starting proxy server on http://localhost:8080..."
cd "$(dirname "$0")"
python3 proxy_server.py &
PROXY_PID=$!

# Wait a moment for proxy to start
sleep 2

# Start HTTP server in background
echo "Starting HTTP server on http://localhost:8000..."
cd http
python3 -m http.server 8000 &
HTTP_PID=$!

echo ""
echo "========================================="
echo "Trading Decision App is running!"
echo "========================================="
echo "Proxy Server: http://localhost:8080"
echo "App: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "========================================="
echo ""

# Wait for both processes
wait

