#!/usr/bin/env python3
"""
Debug script to test Flask server and diagnose routing issues
Run this while your Flask server is running
"""
import requests
import json
import sys

def test_flask_server():
    """Test all possible URLs and methods"""
    
    # Different base URLs to try
    base_urls = [
        "http://127.0.0.1:5000",
        "http://localhost:5000", 
        "http://192.168.31.10:5000"
    ]
    
    # Endpoints to test
    endpoints = [
        "",           # Root
        "/",          # Root with slash
        "/health",
        "/test",
        "/tunnel-status",
        "/proxy",
        "/geoserver-proxy"
    ]
    
    print("🔍 Flask Server Debug Test")
    print("=" * 60)
    
    for base_url in base_urls:
        print(f"\n🌐 Testing base URL: {base_url}")
        print("-" * 40)
        
        for endpoint in endpoints:
            full_url = f"{base_url}{endpoint}"
            
            try:
                print(f"Testing: {full_url:<40}", end=" ")
                response = requests.get(full_url, timeout=5)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  ✅ JSON Response: {json.dumps(data, indent=2)[:100]}...")
                    except:
                        content = response.text[:100].replace('\n', ' ')
                        print(f"  ✅ Text Response: {content}...")
                elif response.status_code == 404:
                    print(f"  ❌ 404 Not Found")
                    print(f"     Response: {response.text[:100]}")
                else:
                    print(f"  ⚠️  Unexpected status: {response.text[:100]}")
                    
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Connection Error: {e}")
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout")
            except Exception as e:
                print(f"❌ Error: {type(e).__name__}: {e}")
        
        print()

def check_server_response_headers():
    """Check response headers to see what server is actually responding"""
    print("\n🔍 Checking Server Response Headers")
    print("=" * 50)
    
    test_urls = [
        "http://127.0.0.1:5000/",
        "http://127.0.0.1:5000/health",
        "http://127.0.0.1:5000/nonexistent"
    ]
    
    for url in test_urls:
        try:
            print(f"\nTesting: {url}")
            response = requests.get(url, timeout=5)
            
            print(f"Status Code: {response.status_code}")
            print(f"Server Header: {response.headers.get('Server', 'Not specified')}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
            print(f"Content-Length: {response.headers.get('Content-Length', 'Not specified')}")
            
            if 'html' in response.headers.get('Content-Type', '').lower():
                print("⚠️  Getting HTML response (might be a different server)")
                if '<title>' in response.text:
                    title_start = response.text.find('<title>') + 7
                    title_end = response.text.find('</title>')
                    if title_end > title_start:
                        title = response.text[title_start:title_end]
                        print(f"Page Title: {title}")
            
        except Exception as e:
            print(f"Error testing {url}: {e}")

def test_with_different_methods():
    """Test with different HTTP methods"""
    print("\n🔍 Testing Different HTTP Methods")
    print("=" * 40)
    
    url = "http://127.0.0.1:5000/health"
    methods = ['GET', 'POST', 'OPTIONS']
    
    for method in methods:
        try:
            print(f"Testing {method} {url}", end=" ")
            if method == 'GET':
                response = requests.get(url, timeout=5)
            elif method == 'POST':
                response = requests.post(url, timeout=5)
            elif method == 'OPTIONS':
                response = requests.options(url, timeout=5)
            
            print(f"-> {response.status_code}")
            
        except Exception as e:
            print(f"-> Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Flask Server Debug Session")
    print("Make sure your Flask server is running on port 5000")
    print("Press Ctrl+C to stop\n")
    
    try:
        test_flask_server()
        check_server_response_headers()
        test_with_different_methods()
        
        print("\n" + "=" * 60)
        print("💡 Troubleshooting Tips:")
        print("1. Check if another service is running on port 5000")
        print("2. Try accessing http://192.168.31.10:5000/health directly")
        print("3. Check Windows Firewall settings")
        print("4. Try running Flask on a different port (5001, 8000, etc.)")
        print("5. Check if antivirus software is blocking requests")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Debug session stopped")