#!/usr/bin/env python3
"""Test job discovery functionality after fixes"""

import sys
import os
import requests
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_job_discovery_endpoints():
    """Test job discovery endpoints"""
    base_url = "http://localhost:8000/api/v1"
    
    # First, register a test user
    print("🔍 Testing Job Discovery Endpoints...")
    
    # Test user registration
    reg_data = {
        "email": f"jobtest_{int(time.time())}@example.com",
        "password": "TestPass123!",
        "first_name": "Job",
        "last_name": "Tester"
    }
    
    try:
        print("1. Registering test user...")
        reg_response = requests.post(f"{base_url}/auth/register", json=reg_data, timeout=10)
        
        if reg_response.status_code not in [201, 400]:
            print(f"❌ Registration failed: {reg_response.status_code}")
            print(f"Response: {reg_response.text}")
            return False
        
        # Login to get token
        print("2. Logging in...")
        login_data = {
            "email": reg_data["email"],
            "password": reg_data["password"]
        }
        
        login_response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test job discovery
        print("3. Testing job discovery...")
        discover_response = requests.post(f"{base_url}/jobs/discover", json={}, headers=headers, timeout=15)
        
        print(f"Discover jobs status: {discover_response.status_code}")
        print(f"Discover response: {discover_response.text}")
        
        if discover_response.status_code == 200:
            print("✅ Job discovery endpoint working!")
        else:
            print("❌ Job discovery failed")
            return False
        
        # Test recommendations generation
        print("4. Testing recommendations generation...")
        rec_response = requests.post(f"{base_url}/jobs/recommendations/generate", json={}, headers=headers, timeout=15)
        
        print(f"Generate recommendations status: {rec_response.status_code}")
        print(f"Generate recommendations response: {rec_response.text}")
        
        if rec_response.status_code == 200:
            print("✅ Recommendations generation endpoint working!")
        else:
            print("❌ Recommendations generation failed")
            return False
        
        # Test getting recommendations
        print("5. Testing get recommendations...")
        get_rec_response = requests.get(f"{base_url}/jobs/recommendations", headers=headers, timeout=10)
        
        print(f"Get recommendations status: {get_rec_response.status_code}")
        print(f"Get recommendations response: {get_rec_response.text}")
        
        if get_rec_response.status_code == 200:
            print("✅ Get recommendations endpoint working!")
            return True
        else:
            print("❌ Get recommendations failed")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_orchestrator_connection():
    """Test if orchestrator is working"""
    try:
        from app.core.orchestrator import orchestrator
        from app.core.orchestrator import TaskPriority
        
        print("🔍 Testing orchestrator connection...")
        
        # Check if job discovery agent is registered
        if "job_discovery_agent" in orchestrator.agents:
            print("✅ Job Discovery Agent is registered")
        else:
            print("❌ Job Discovery Agent is NOT registered")
            print(f"Available agents: {list(orchestrator.agents.keys())}")
            return False
        
        # Test creating a task
        task_data = {
            "user_id": "test_user",
            "search_params": {}
        }
        
        task_id = await orchestrator.create_task(
            agent_id="job_discovery_agent",
            task_type="discover_jobs",
            payload=task_data,
            priority=TaskPriority.MEDIUM
        )
        
        print(f"✅ Task created successfully: {task_id}")
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Job Discovery Fixes...")
    print("=" * 50)
    
    # Test API endpoints
    api_success = test_job_discovery_endpoints()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)
    
    if api_success:
        print("🎉 Job Discovery API endpoints are working!")
        print("\nNext steps:")
        print("1. The job discovery should now work when clicking 'Discover New Jobs'")
        print("2. The system will process jobs in the background")
        print("3. Check back in a few moments for new recommendations")
    else:
        print("💥 Some issues remain with job discovery")
        print("\nTroubleshooting:")
        print("1. Make sure the backend server is running")
        print("2. Check that all agents are properly registered")
        print("3. Verify the orchestrator is working correctly")