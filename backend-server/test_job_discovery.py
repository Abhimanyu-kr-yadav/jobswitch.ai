#!/usr/bin/env python3
"""
Test script to verify job discovery functionality
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """Get authentication token"""
    try:
        login_data = {
            "email": "abhi@test.com",
            "password": "TestPassword123"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {str(e)}")
        return None

def test_job_discovery(token):
    """Test job discovery endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE_URL}/jobs/discover", json={}, headers=headers)
        print(f"✅ Job Discovery: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Job Discovery failed: {str(e)}")
        return False

def test_job_recommendations(token):
    """Test job recommendations endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/jobs/recommendations", headers=headers)
        print(f"✅ Job Recommendations: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('recommendations', []))} recommendations")
        else:
            print(f"   Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Job Recommendations failed: {str(e)}")
        return False

def test_job_search(token):
    """Test job search endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": "software engineer"}
        response = requests.get(f"{API_BASE_URL}/jobs/search", params=params, headers=headers)
        print(f"✅ Job Search: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('jobs', []))} jobs")
        else:
            print(f"   Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Job Search failed: {str(e)}")
        return False

def test_generate_recommendations(token):
    """Test recommendation generation"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE_URL}/jobs/recommendations/generate", json={}, headers=headers)
        print(f"✅ Generate Recommendations: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Generate Recommendations failed: {str(e)}")
        return False

def main():
    print("🚀 Testing JobSwitch.ai Job Discovery System")
    print("=" * 50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return
    
    print(f"✅ Authentication successful")
    print("\n🔍 Testing Job Discovery Endpoints")
    print("-" * 30)
    
    # Test job discovery
    test_job_discovery(token)
    
    # Test job recommendations
    test_job_recommendations(token)
    
    # Test job search
    test_job_search(token)
    
    # Test recommendation generation
    test_generate_recommendations(token)
    
    print("\n🎉 Job Discovery system testing complete!")

if __name__ == "__main__":
    main()