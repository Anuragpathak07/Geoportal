#!/usr/bin/env python3
"""
Fixed Flask Configuration Server
Provides ngrok tunnel configuration and saves to JSON file
"""
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

def save_config_to_file(config_data, filename='ngrok_urls.json'):
    """Save configuration data to JSON file with error handling"""
    try:
        # Add timestamp to the config
        config_with_timestamp = {
            **config_data,
            'last_updated': datetime.now().isoformat(),
            'server_port': 9000
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(config_with_timestamp, f, indent=2)
        
        print(f"✅ Configuration saved to {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving config to file: {e}")
        return False

@app.route('/')
def home():
    """Home endpoint with server information"""
    return jsonify({
        "message": "Flask Configuration Server",
        "status": "running",
        "port": 9000,
        "endpoints": {
            "/api/config": "Get ngrok tunnel configuration",
            "/api/config/refresh": "Refresh and save configuration",
            "/health": "Health check"
        },
        "usage": {
            "get_config": "GET /api/config",
            "refresh_config": "GET /api/config/refresh"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "flask-config-server"})

@app.route('/api/config')
def config():
    """Get ngrok tunnel configuration"""
    try:
        print("🔍 Fetching ngrok tunnel information...")
        
        # Fixed the IP address typo
        response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=10)
        tunnels = response.json()['tunnels']
        
        config_data = {}
        
        print(f"📡 Found {len(tunnels)} tunnels:")
        
        for tunnel in tunnels:
            name = tunnel.get('name')
            public_url = tunnel.get('public_url')
            proto = tunnel.get('proto', 'unknown')
            
            print(f"  - Tunnel: {name} -> {public_url} ({proto})")
            
            if name == 'geoserver':
                config_data['geoserver_url'] = f"{public_url}/geoserver"
                print(f"    ✅ GeoServer URL set: {config_data['geoserver_url']}")
            elif name == 'flask-proxy':
                config_data['proxy_url'] = public_url
                print(f"    ✅ Flask Proxy URL set: {public_url}")
            elif name == 'html-server':
                config_data['html_server_url'] = public_url
                print(f"    ✅ HTML Server URL set: {public_url}")
            else:
                # Handle any other tunnels
                config_data[f'{name}_url'] = public_url
                print(f"    ℹ️  {name} URL set: {public_url}")
        
        # Add tunnel count and status
        config_data['tunnel_count'] = len(tunnels)
        config_data['ngrok_status'] = 'active'
        
        print("\n--- FINAL CONFIGURATION ---")
        for key, value in config_data.items():
            print(f"{key}: {value}")
        print("--- END CONFIGURATION ---\n")
        
        return jsonify(config_data)
        
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to ngrok API at http://127.0.0.1:4040"
        print(f"❌ {error_msg}")
        print("   Make sure ngrok is running with: ngrok http 8080")
        return jsonify({
            "error": error_msg,
            "ngrok_status": "not_running",
            "suggestion": "Start ngrok with: ngrok http 8080"
        }), 503
        
    except requests.exceptions.Timeout:
        error_msg = "Timeout connecting to ngrok API"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 504
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to ngrok API: {e}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500
        
    except KeyError as e:
        error_msg = f"Invalid response from ngrok API: missing {e}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 502
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/api/config/refresh')
def refresh_config():
    """Refresh configuration and save to file"""
    try:
        print("🔄 Refreshing configuration...")
        
        # Get the current configuration
        with app.test_client() as client:
            response = client.get('/api/config')
            
        if response.status_code == 200:
            config_data = response.get_json()
            
            # Save to file
            if save_config_to_file(config_data):
                return jsonify({
                    "status": "success",
                    "message": "Configuration refreshed and saved",
                    "config": config_data,
                    "file_saved": True
                })
            else:
                return jsonify({
                    "status": "partial_success", 
                    "message": "Configuration refreshed but file save failed",
                    "config": config_data,
                    "file_saved": False
                })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to refresh configuration",
                "details": response.get_json()
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Refresh failed: {e}"
        }), 500

@app.route('/api/config/file')
def get_saved_config():
    """Get configuration from saved file"""
    try:
        if os.path.exists('ngrok_urls.json'):
            with open('ngrok_urls.json', 'r') as f:
                config = json.load(f)
            return jsonify({
                "status": "success",
                "source": "file",
                "config": config
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No saved configuration file found"
            }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error reading config file: {e}"
        }), 500

def startup_check():
    """Check system status on startup"""
    print("=" * 60)
    print("🚀 FLASK CONFIGURATION SERVER STARTING")
    print("=" * 60)
    
    # Check if ngrok is running
    try:
        response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
        tunnels = response.json()['tunnels']
        print(f"✅ Ngrok is running with {len(tunnels)} tunnels")
        
        # Try to save initial configuration
        if tunnels:
            print("💾 Saving initial configuration...")
            with app.app_context():
                with app.test_client() as client:
                    config_response = client.get('/api/config')
                    if config_response.status_code == 200:
                        save_config_to_file(config_response.get_json())
        
    except Exception as e:
        print(f"⚠️  Ngrok not accessible: {e}")
        print("   You can start ngrok later and refresh the config")
    
    print(f"🌐 Server starting on: http://localhost:9000")
    print(f"📋 Configuration endpoint: http://localhost:9000/api/config")
    print(f"🔄 Refresh endpoint: http://localhost:9000/api/config/refresh")
    print("=" * 60)

if __name__ == '__main__':
    startup_check()
    
    try:
        app.run(
            host='0.0.0.0',  # Allow connections from other machines
            port=9000, 
            debug=True,
            use_reloader=False  # Prevent double startup messages
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        print("🔚 Configuration server shutdown")