#!/usr/bin/env python3
"""Check which port the backend server is running on"""

import sys
import os
import socket
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False  # Port is available
        except OSError:
            return True   # Port is in use

def test_server_on_port(port):
    """Test if the JobSwitch server is running on a specific port"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if "JobSwitch" in str(data) or "overall_status" in data:
                return True
    except:
        pass
    return False

def find_backend_port():
    """Find which port the backend is running on"""
    print("🔍 Checking for JobSwitch.ai backend server...")
    
    # Check configuration default
    try:
        from app.core.config import settings
        config_port = settings.api_port
        print(f"📋 Configuration default port: {config_port}")
        
        if check_port_in_use(config_port):
            print(f"✅ Port {config_port} is in use")
            if test_server_on_port(config_port):
                print(f"🎯 JobSwitch.ai backend found on port {config_port}")
                return config_port
            else:
                print(f"⚠️  Port {config_port} in use but not JobSwitch.ai")
        else:
            print(f"❌ Port {config_port} is not in use")
    except Exception as e:
        print(f"❌ Could not read configuration: {e}")
        config_port = 8000
    
    # Check common ports
    common_ports = [8000, 8080, 3000, 5000, 8001, 8888]
    if config_port not in common_ports:
        common_ports.insert(0, config_port)
    
    print(f"\n🔍 Checking common ports: {common_ports}")
    
    for port in common_ports:
        if check_port_in_use(port):
            print(f"✅ Port {port} is in use", end=" - ")
            if test_server_on_port(port):
                print("🎯 JobSwitch.ai backend found!")
                return port
            else:
                print("❌ Not JobSwitch.ai")
        else:
            print(f"❌ Port {port} is not in use")
    
    print("\n❌ JobSwitch.ai backend not found on any common port")
    return None

def show_server_info(port):
    """Show detailed server information"""
    if not port:
        print("❌ No server found")
        return
    
    print(f"\n{'='*50}")
    print(f"🎯 JobSwitch.ai Backend Server Found")
    print(f"{'='*50}")
    print(f"Port: {port}")
    print(f"Base URL: http://localhost:{port}")
    print(f"Health Check: http://localhost:{port}/health")
    print(f"API Base: http://localhost:{port}/api/v1")
    print(f"Documentation: http://localhost:{port}/docs")
    
    # Test key endpoints
    endpoints = [
        ("/", "Root"),
        ("/health", "Health Check"),
        ("/api/v1/auth/register", "Registration"),
        ("/docs", "API Documentation")
    ]
    
    print(f"\n📋 Endpoint Status:")
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://localhost:{port}{endpoint}", timeout=3)
            status = "✅" if response.status_code < 400 else "⚠️"
            print(f"  {status} {name}: {response.status_code}")
        except:
            print(f"  ❌ {name}: Not accessible")

if __name__ == "__main__":
    port = find_backend_port()
    show_server_info(port)
    
    if port:
        print(f"\n🚀 Your backend is running on port {port}")
        print(f"   Access it at: http://localhost:{port}")
    else:
        print(f"\n💡 To start the backend server:")
        print(f"   cd backend-server")
        print(f"   python app/main.py")
        print(f"   # or")
        print(f"   uvicorn app.main:app --host 0.0.0.0 --port 8000")