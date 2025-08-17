#!/usr/bin/env python3
"""
Test script to verify authentication endpoints are working
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

def test_user_registration():
    """Test user registration"""
    try:
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890",
            "location": "New York, NY"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/register", json=user_data)
        print(f"✅ User registration: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ User registration failed: {str(e)}")
        return False

def test_user_login():
    """Test user login"""
    try:
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
        print(f"✅ User login: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Access token received: {len(data.get('access_token', ''))} chars")
            return data.get('access_token')
        else:
            print(f"   Response: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ User login failed: {str(e)}")
        return None

def test_protected_endpoint(token):
    """Test accessing protected endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
        print(f"✅ Protected endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   User: {data.get('first_name')} {data.get('last_name')}")
            print(f"   Email: {data.get('email')}")
            print(f"   Profile completion: {data.get('profile_completion', 0) * 100}%")
        else:
            print(f"   Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Protected endpoint failed: {str(e)}")
        return False

def test_profile_update(token):
    """Test profile update"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        profile_data = {
            "current_title": "Software Engineer",
            "current_company": "Tech Corp",
            "years_experience": 5,
            "industry": "Technology"
        }
        
        response = requests.put(f"{API_BASE_URL}/user/profile", json=profile_data, headers=headers)
        print(f"✅ Profile update: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Profile update failed: {str(e)}")
        return False

def main():
    print("🚀 Testing JobSwitch.ai Authentication System")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test health endpoint
    if not test_health_endpoint():
        print("❌ Server is not running. Please start the server first.")
        return
    
    print("\n📝 Testing Authentication Endpoints")
    print("-" * 30)
    
    # Test registration
    test_user_registration()
    
    # Test login
    token = test_user_login()
    
    if token:
        print("\n🔒 Testing Protected Endpoints")
        print("-" * 30)
        
        # Test protected endpoint
        test_protected_endpoint(token)
        
        # Test profile update
        test_profile_update(token)
    
    print("\n🎉 Authentication system testing complete!")

if __name__ == "__main__":
    main()