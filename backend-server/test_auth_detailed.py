#!/usr/bin/env python3
"""Detailed test to debug authentication issues"""

import requests
import json
import sys

def test_registration_detailed():
    """Test user registration with detailed error reporting"""
    url = "http://localhost:8000/api/v1/auth/register"
    data = {
        "email": "debug_user@example.com",
        "password": "TestPass123!",
        "first_name": "Debug",
        "last_name": "User"
    }
    
    try:
        print("Testing user registration with detailed logging...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        elif response.status_code == 400:
            response_data = response.json()
            if "already exists" in response_data.get("error", {}).get("message", ""):
                print("✅ Registration endpoint working (user already exists)")
                return True
            else:
                print(f"❌ Registration failed with validation error: {response_data}")
                return False
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_health_check():
    """Test if the server is responding"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        print(f"Health response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_simple_endpoint():
    """Test a simple endpoint to see if the server is working"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"Root endpoint status: {response.status_code}")
        print(f"Root response: {response.text}")
        return True
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Detailed Authentication Debug Test ===\n")
    
    print("1. Testing server health...")
    health_ok = test_health_check()
    print()
    
    print("2. Testing simple endpoint...")
    simple_ok = test_simple_endpoint()
    print()
    
    print("3. Testing registration endpoint...")
    reg_ok = test_registration_detailed()
    print()
    
    if health_ok and simple_ok and reg_ok:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed")
        sys.exit(1)