#!/usr/bin/env python3
"""
Proxy server for Trading Decision App
Handles CORS issues by proxying requests to data provider APIs
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Rate limiting: track requests per API key
rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 100  # per API key per minute

def check_rate_limit(api_key):
    """Check if API key has exceeded rate limit"""
    if not api_key:
        return True
    
    now = time.time()
    key_requests = rate_limit_store[api_key]
    
    # Remove requests outside the time window
    key_requests[:] = [req_time for req_time in key_requests if now - req_time < RATE_LIMIT_WINDOW]
    
    if len(key_requests) >= MAX_REQUESTS_PER_WINDOW:
        return False
    
    key_requests.append(now)
    return True

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'trading-decision-app-proxy'
    })

@app.route('/api/proxy', methods=['POST', 'OPTIONS'])
def proxy():
    """Proxy endpoint that forwards requests to target APIs"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No request data provided'}), 400
        
        target_url = data.get('url')
        method = data.get('method', 'GET').upper()
        headers = data.get('headers', {})
        body = data.get('body')
        params = data.get('params', {})
        
        if not target_url:
            return jsonify({'error': 'Target URL is required'}), 400
        
        # Extract API key from headers for rate limiting
        api_key = headers.get('apikey') or headers.get('api_key') or headers.get('token') or params.get('apikey') or params.get('api_key') or params.get('token')
        
        # Check rate limit
        if not check_rate_limit(api_key):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Maximum {MAX_REQUESTS_PER_WINDOW} requests per {RATE_LIMIT_WINDOW} seconds'
            }), 429
        
        # Prepare request
        request_kwargs = {
            'method': method,
            'url': target_url,
            'headers': headers,
            'timeout': 30
        }
        
        # Add params for GET requests or if specified
        if params:
            request_kwargs['params'] = params
        
        # Add body for POST/PUT/PATCH requests
        if body and method in ['POST', 'PUT', 'PATCH']:
            if isinstance(body, dict):
                request_kwargs['json'] = body
            else:
                request_kwargs['data'] = body
        
        # Make the request
        response = requests.request(**request_kwargs)
        
        # Return response with CORS headers
        return jsonify({
            'status': response.status_code,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'headers': dict(response.headers)
        }), response.status_code
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout', 'message': 'The API request took too long'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection error', 'message': 'Could not connect to the target API'}), 502
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Request failed', 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Proxy error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'The requested endpoint does not exist'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting proxy server on {host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"Proxy endpoint: http://{host}:{port}/api/proxy")
    
    app.run(host=host, port=port, debug=debug)

