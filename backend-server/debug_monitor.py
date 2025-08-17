#!/usr/bin/env python3
"""Real-time debugging and monitoring utilities"""

import sys
import os
import time
import requests
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class RealTimeMonitor:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.monitoring = True
    
    def monitor_health(self, interval=30):
        """Monitor server health in real-time"""
        print("🔍 Starting real-time health monitoring...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.monitoring:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    if response.status_code == 200:
                        health = response.json()
                        status = health.get('overall_status', 'unknown')
                        uptime = health.get('uptime_seconds', 0)
                        
                        print(f"[{timestamp}] Status: {status}, Uptime: {uptime:.1f}s")
                    else:
                        print(f"[{timestamp}] ❌ Health check failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"[{timestamp}] ❌ Server unreachable: {e}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
    
    def test_endpoint_continuously(self, endpoint, method="GET", data=None, interval=10):
        """Test a specific endpoint continuously"""
        print(f"🔍 Monitoring endpoint: {method} {endpoint}")
        print("Press Ctrl+C to stop\n")
        
        success_count = 0
        total_count = 0
        
        try:
            while self.monitoring:
                timestamp = datetime.now().strftime("%H:%M:%S")
                total_count += 1
                
                try:
                    response = requests.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        json=data,
                        timeout=10
                    )
                    
                    if response.status_code < 400:
                        success_count += 1
                        print(f"[{timestamp}] ✅ {response.status_code} - Success rate: {success_count/total_count*100:.1f}%")
                    else:
                        print(f"[{timestamp}] ❌ {response.status_code} - {response.text[:100]}")
                        
                except Exception as e:
                    print(f"[{timestamp}] ❌ Request failed: {e}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped. Final success rate: {success_count/total_count*100:.1f}%")

def debug_specific_error(error_type):
    """Debug specific types of errors"""
    print(f"🔍 Debugging {error_type} errors...")
    
    if error_type == "auth":
        # Test authentication flow step by step
        print("Testing authentication flow...")
        
        # Step 1: Test registration
        reg_data = {
            "email": f"debug_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "first_name": "Debug",
            "last_name": "User"
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/auth/register",
                json=reg_data,
                timeout=10
            )
            print(f"Registration: {response.status_code}")
            if response.status_code >= 400:
                print(f"Error: {response.text}")
                return
            
            # Step 2: Test login
            login_data = {
                "email": reg_data["email"],
                "password": reg_data["password"]
            }
            
            response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            print(f"Login: {response.status_code}")
            if response.status_code >= 400:
                print(f"Error: {response.text}")
                return
            
            print("✅ Authentication flow working")
            
        except Exception as e:
            print(f"❌ Authentication debug failed: {e}")
    
    elif error_type == "database":
        # Test database operations
        try:
            from app.core.database import db_manager
            from app.models.user import UserProfile
            
            session = db_manager.get_session()
            
            # Test query
            users = session.query(UserProfile).limit(5).all()
            print(f"✅ Database query successful: {len(users)} users found")
            
            session.close()
            
        except Exception as e:
            print(f"❌ Database debug failed: {e}")
    
    elif error_type == "models":
        # Test model relationships
        try:
            from app.models.user import UserProfile
            from app.models.analytics import JobSearchMetrics
            
            # Test model creation
            from sqlalchemy import create_engine
            from app.models.base import Base
            
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            
            print("✅ Model relationships working")
            
        except Exception as e:
            print(f"❌ Model debug failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "health":
            monitor = RealTimeMonitor()
            monitor.monitor_health()
        elif command == "auth":
            debug_specific_error("auth")
        elif command == "database":
            debug_specific_error("database")
        elif command == "models":
            debug_specific_error("models")
        elif command.startswith("endpoint:"):
            endpoint = command.split(":", 1)[1]
            monitor = RealTimeMonitor()
            monitor.test_endpoint_continuously(endpoint)
        else:
            print("Usage: python debug_monitor.py [health|auth|database|models|endpoint:/path]")
    else:
        print("Available debugging commands:")
        print("  python debug_monitor.py health          - Monitor server health")
        print("  python debug_monitor.py auth            - Debug authentication")
        print("  python debug_monitor.py database        - Debug database")
        print("  python debug_monitor.py models          - Debug models")
        print("  python debug_monitor.py endpoint:/path  - Monitor specific endpoint")