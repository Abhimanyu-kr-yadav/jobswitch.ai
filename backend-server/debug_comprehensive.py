#!/usr/bin/env python3
"""Comprehensive debugging script for JobSwitch.ai"""

import sys
import os
import requests
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class JobSwitchDebugger:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {}
    
    def debug_all(self):
        """Run all debug tests"""
        print("🔍 Starting comprehensive debugging...\n")
        
        tests = [
            ("Server Health", self.test_server_health),
            ("Database Models", self.test_database_models),
            ("Authentication", self.test_authentication),
            ("API Endpoints", self.test_api_endpoints),
            ("Agent System", self.test_agent_system),
        ]
        
        for test_name, test_func in tests:
            print(f"{'='*50}")
            print(f"Testing: {test_name}")
            print(f"{'='*50}")
            
            try:
                result = test_func()
                self.results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"{status}: {test_name}\n")
            except Exception as e:
                print(f"❌ ERROR in {test_name}: {e}\n")
                self.results[test_name] = False
        
        self.print_summary()
    
    def test_server_health(self):
        """Test if server is running and healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"Server Status: {health_data.get('overall_status', 'unknown')}")
                print(f"Version: {health_data.get('version', 'unknown')}")
                return True
            else:
                print(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Server not accessible: {e}")
            return False
    
    def test_database_models(self):
        """Test database model imports and relationships"""
        try:
            from app.models.base import Base
            from app.models.user import UserProfile
            from app.models.analytics import JobSearchMetrics
            from app.models.job import Job
            
            # Test database creation
            from sqlalchemy import create_engine
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            
            print("✅ All models imported and database schema created")
            return True
        except Exception as e:
            print(f"Model error: {e}")
            return False
    
    def test_authentication(self):
        """Test authentication endpoints"""
        # Test registration
        reg_data = {
            "email": f"debug_{datetime.now().timestamp()}@example.com",
            "password": "TestPass123!",
            "first_name": "Debug",
            "last_name": "User"
        }
        
        try:
            reg_response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=reg_data,
                timeout=10
            )
            
            if reg_response.status_code in [201, 400]:  # 400 if user exists
                print("✅ Registration endpoint working")
                
                # Test login
                login_data = {
                    "email": reg_data["email"],
                    "password": reg_data["password"]
                }
                
                login_response = requests.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json=login_data,
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    print("✅ Login endpoint working")
                    return True
                else:
                    print(f"Login failed: {login_response.status_code}")
                    print(f"Response: {login_response.text}")
                    return False
            else:
                print(f"Registration failed: {reg_response.status_code}")
                print(f"Response: {reg_response.text}")
                return False
                
        except Exception as e:
            print(f"Authentication test error: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test key API endpoints"""
        endpoints = [
            ("/", "GET"),
            ("/api/v1/jobs/search", "GET"),
            ("/api/v1/skills/analyze", "GET"),
        ]
        
        working_endpoints = 0
        
        for endpoint, method in endpoints:
            try:
                response = requests.request(
                    method, 
                    f"{self.base_url}{endpoint}",
                    timeout=5
                )
                if response.status_code < 500:  # Not server error
                    working_endpoints += 1
                    print(f"✅ {endpoint} ({response.status_code})")
                else:
                    print(f"❌ {endpoint} ({response.status_code})")
            except Exception as e:
                print(f"❌ {endpoint} (Error: {e})")
        
        return working_endpoints > len(endpoints) // 2
    
    def test_agent_system(self):
        """Test AI agent system"""
        try:
            from app.core.orchestrator import orchestrator
            from app.agents.base import BaseAgent
            
            print("✅ Agent system imports working")
            
            # Test if orchestrator is initialized
            if hasattr(orchestrator, 'agents'):
                print(f"✅ Orchestrator initialized with {len(orchestrator.agents)} agents")
                return True
            else:
                print("❌ Orchestrator not properly initialized")
                return False
                
        except Exception as e:
            print(f"Agent system error: {e}")
            return False
    
    def print_summary(self):
        """Print debugging summary"""
        print("\n" + "="*60)
        print("DEBUGGING SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All systems working correctly!")
        else:
            print("💥 Some systems need attention")
            print("\nNext steps:")
            for test_name, result in self.results.items():
                if not result:
                    print(f"- Fix issues in: {test_name}")

if __name__ == "__main__":
    debugger = JobSwitchDebugger()
    debugger.debug_all()