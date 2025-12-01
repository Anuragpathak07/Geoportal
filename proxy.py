#!/usr/bin/env python3
"""
Enhanced Flask proxy with complete ngrok warning bypass and configuration endpoint
This handles both the browser warning and programmatic access, plus provides tunnel configuration
"""
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
import logging
import json
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "ngrok-skip-browser-warning"]
    }
})

def get_ngrok_bypass_headers():
    """Get headers to bypass ngrok warnings completely"""
    return {
        'ngrok-skip-browser-warning': 'true',
        'ngrok-skip-browser-warning': 'any',  # Some versions need this
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, application/xml, text/xml, text/html, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    }

@app.route('/')
def home():
    """Root endpoint with ngrok testing info"""
    return jsonify({
        "message": "Enhanced Ngrok Proxy Server with Configuration",
        "status": "healthy",
        "ngrok_bypass": "Enabled with complete headers",
        "endpoints": {
            "/health": "Health check",
            "/test": "Server status", 
            "/tunnel-status": "Check ngrok tunnels",
            "/api/config": "Get ngrok tunnel configuration",
            "/proxy": "General proxy with ngrok bypass",
            "/geoserver-proxy": "GeoServer-specific proxy",
            "/test-ngrok": "Test ngrok bypass directly"
        },
        "usage": {
            "config": "/api/config",
            "proxy": "/proxy?url=https://1423-2409-40c2-4011-f4d6-6974-cecc-2983-e0b3.ngrok-free.app/",
            "geoserver": "/geoserver-proxy?base_url=https://1423-2409-40c2-4011-f4d6-6974-cecc-2983-e0b3.ngrok-free.app/&layer=India Boundary"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "enhanced-ngrok-proxy"})

@app.route('/api/config')
def config():
    """Get ngrok tunnel configuration - integrated from the second code"""
    try:
        print("Fetching ngrok tunnel information...")
        tunnels = requests.get('http://127.0.0.1:4040/api/tunnels').json()['tunnels']
        
        config = {}
        
        print(f"Found {len(tunnels)} tunnels:")
        
        for tunnel in tunnels:
            name = tunnel.get('name')
            public_url = tunnel.get('public_url')
            
            print(f"  - Tunnel: {name} -> {public_url}")
            
            if name == 'geoserver':
                config['geoserver_url'] = f"{public_url}/geoserver"
                print(f"    ✓ GeoServer URL set: {config['geoserver_url']}")
            elif name == 'flask-proxy':
                config['proxy_url'] = public_url
                print(f"    ✓ Flask Proxy URL set: {public_url}")
            elif name == 'html-server':
                config['html_server_url'] = public_url
                print(f"    ✓ HTML Server URL set: {public_url}")
        
        print("\n--- FINAL CONFIGURATION ---")
        for key, value in config.items():
            print(f"{key}: {value}")
        print("--- END CONFIGURATION ---\n")
        
        return jsonify(config)
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to ngrok API: {e}")
        print("Make sure ngrok is running and accessible at http://127.0.0.1:4040")
        return jsonify({"error": "Could not connect to ngrok API"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-ngrok')
def test_ngrok():
    """Test endpoint to verify ngrok bypass works"""
    test_url = request.args.get('url')
    if not test_url:
        return jsonify({
            "error": "Missing 'url' parameter",
            "usage": "/test-ngrok?url=YOUR_NGROK_URL",
            "example": "/test-ngrok?url=https://abc123.ngrok-free.app/geoserver/web"
        }), 400
    
    logging.info(f"Testing ngrok bypass for: {test_url}")
    
    try:
        headers = get_ngrok_bypass_headers()
        response = requests.get(test_url, headers=headers, timeout=15)
        
        is_warning_page = (
            'ngrok.com' in response.text.lower() and 
            'visit this website' in response.text.lower()
        ) or 'ERR_NGROK_6024' in response.text
        
        return jsonify({
            "url": test_url,
            "status_code": response.status_code,
            "content_type": response.headers.get('Content-Type'),
            "is_ngrok_warning": is_warning_page,
            "bypass_success": not is_warning_page,
            "response_size": len(response.content),
            "headers_sent": headers
        })
        
    except Exception as e:
        return jsonify({
            "error": "Test failed",
            "details": str(e),
            "url": test_url
        }), 500

@app.route('/proxy', methods=['GET', 'POST'])
def proxy():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({
            "error": "Missing 'url' parameter",
            "usage": "/proxy?url=TARGET_URL",
            "example": "/proxy?url=https://your-ngrok-url.ngrok-free.app/geoserver/web"
        }), 400

    # Decode URL if it's encoded
    target_url = urllib.parse.unquote(target_url)
    logging.info(f"Target URL: {target_url}")

    # Prepare headers, excluding 'Host'
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}

    try:
        if request.method == 'POST':
            # Forward POST with data and headers
            resp = requests.post(target_url, data=request.data, headers=headers, timeout=30, allow_redirects=True)
        else:
            # Forward GET with headers and params
            params = {k: v for k, v in request.args.items() if k != 'url'}
            resp = requests.get(target_url, params=params, headers=headers, timeout=30, allow_redirects=True)

        # Prepare response headers (exclude hop-by-hop headers)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in resp.headers.items() if name.lower() not in excluded_headers]

        # Add CORS headers
        response_headers.append(('Access-Control-Allow-Origin', '*'))
        response_headers.append(('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'))
        response_headers.append(('Access-Control-Allow-Headers', 'Content-Type, Authorization, ngrok-skip-browser-warning'))
        response_headers.append(('Access-Control-Expose-Headers', 'Content-Length, Content-Type'))

        return Response(resp.content, resp.status_code, response_headers)

    except requests.exceptions.Timeout:
        logging.error("Request timeout")
        return jsonify({"error": "Request timeout"}), 504

    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error: {e}")
        return jsonify({"error": "Connection error", "details": str(e)}), 502

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Proxy error", "details": str(e)}), 500

@app.route('/geoserver-proxy')
def geoserver_proxy():
    """GeoServer-specific proxy with ngrok bypass"""
    # Get parameters
    base_url = request.args.get('base_url')
    layer_name = request.args.get('layer')
    
    if not base_url or not layer_name:
        return jsonify({
            "error": "Missing required parameters",
            "required": ["base_url", "layer"],
            "example": "/geoserver-proxy?base_url=https://your-ngrok-url.ngrok-free.app&layer=India%20Boundary"
        }), 400
    
    # Default GeoServer WFS parameters
    params = {
        'service': 'WFS',
        'version': '1.1.0',
        'request': 'GetFeature',
        'typeName': f'allshapefiles:{layer_name}',
        'outputFormat': 'application/json',
        'srsName': 'EPSG:4326'
    }
    
    # Add any additional parameters
    for key, value in request.args.items():
        if key not in ['base_url', 'layer']:
            params[key] = value
    
    # Build the full GeoServer URL
    geoserver_url = f"{base_url.rstrip('/')}/geoserver/allshapefiles/wfs"
    
    logging.info(f"GeoServer proxy request: {geoserver_url}")
    logging.info(f"Parameters: {params}")
    
    try:
        headers = get_ngrok_bypass_headers()
        
        response = requests.get(
            geoserver_url,
            params=params,
            headers=headers,
            timeout=30
        )
        
        # Check for ngrok warning
        if 'text/html' in response.headers.get('Content-Type', '').lower():
            if 'ngrok.com' in response.text.lower() and 'visit this website' in response.text.lower():
                return jsonify({
                    "error": "Ngrok warning page",
                    "message": "GeoServer URL is showing ngrok browser warning",
                    "geoserver_url": geoserver_url,
                    "suggestion": "Try accessing the GeoServer URL directly first"
                }), 502
        
        return Response(
            response.content,
            status=response.status_code,
            headers={
                'Content-Type': response.headers.get('Content-Type', 'application/json'),
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, ngrok-skip-browser-warning'
            }
        )
        
    except Exception as e:
        return jsonify({
            "error": "GeoServer proxy error", 
            "details": str(e),
            "geoserver_url": geoserver_url
        }), 500

@app.route('/tunnel-status')
def tunnel_status():
    """Check ngrok tunnel status - enhanced version"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        tunnels = response.json()
        
        active_tunnels = {}
        tunnel_details = []
        
        for tunnel in tunnels.get('tunnels', []):
            name = tunnel.get('name', 'unknown')
            public_url = tunnel.get('public_url', 'unknown')
            proto = tunnel.get('proto', 'unknown')
            config = tunnel.get('config', {})
            
            active_tunnels[name] = public_url
            tunnel_details.append({
                'name': name,
                'public_url': public_url,
                'protocol': proto,
                'local_addr': config.get('addr', 'unknown')
            })
            
        return jsonify({
            "status": "success",
            "active_tunnels": active_tunnels,
            "tunnel_details": tunnel_details,
            "total_tunnels": len(active_tunnels),
            "ngrok_bypass": "Headers configured for all requests",
            "ngrok_api_url": "http://localhost:4040/api/tunnels"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Could not connect to ngrok API",
            "details": str(e),
            "suggestion": "Make sure ngrok is running and accessible at http://localhost:4040"
        }), 500

if __name__ == '__main__':
    logging.info("🚀 Starting Enhanced Ngrok Proxy Server with Configuration")
    logging.info("🔧 Features: Complete ngrok warning bypass + tunnel configuration")
    logging.info("🌐 Server: http://0.0.0.0:5000")
    logging.info("📋 Configuration endpoint: /api/config")
    logging.info("📋 Test ngrok bypass: /test-ngrok?url=YOUR_NGROK_URL")
    logging.info("📋 Tunnel status: /tunnel-status")
    logging.info("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)