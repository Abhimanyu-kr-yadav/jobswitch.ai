#!/usr/bin/env python3
"""Test authentication endpoint after model fixes"""

import requests
import json

def test_registration():
    """Test user registration endpoint"""
    url = "http://localhost:8000/api/v1/auth/register"
    data = {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        print("Testing user registration...")
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print("✅ Registration endpoint working (user already exists)")
            return True
        else:
            print("❌ Registration failed")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login():
    """Test user login endpoint"""
    url = "http://localhost:8000/api/v1/auth/login"
    data = {
        "email": "testuser@example.com",
        "password": "TestPass123!"
    }
    
    try:
        print("Testing user login...")
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return True
        else:
            print("❌ Login failed")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing authentication endpoints after model fixes...\n")
    
    # Test registration first
    reg_success = test_registration()
    print()
    
    # Test login
    login_success = test_login()
    print()
    
    if reg_success and login_success:
        print("🎉 All authentication tests passed!")
    else:
        print("💥 Some tests failed - check server logs")