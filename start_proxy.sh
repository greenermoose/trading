#!/bin/bash
# Start the proxy server for Trading Decision App

echo "Starting Trading Decision App Proxy Server..."
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

# Start the proxy server
echo "Proxy server will run on http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""
python3 proxy_server.py

