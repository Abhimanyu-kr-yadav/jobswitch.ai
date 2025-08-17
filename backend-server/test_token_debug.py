#!/usr/bin/env python3
"""
Debug script to test token authentication
"""
import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def test_login_and_me():
    """Test login and then /me endpoint"""
    try:
        # Login
        login_data = {
            "email": "abhi@test.com",
            "password": "TestPassword123"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"Token received: {token[:50]}...")
            
            # Test /me endpoint
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
            print(f"/me response: {me_response.status_code}")
            
            if me_response.status_code == 200:
                print(f"User data: {me_response.json()}")
            else:
                print(f"Error: {me_response.text}")
                
        else:
            print(f"Login failed: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_login_and_me()