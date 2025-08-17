#!/usr/bin/env python3
"""Component-specific debugging utilities"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_database():
    """Debug database connections and queries"""
    print("🔍 Debugging Database...")
    
    try:
        from app.core.database import db_manager
        from app.models.user import UserProfile
        
        # Test connection
        if db_manager.check_connection():
            print("✅ Database connection working")
        else:
            print("❌ Database connection failed")
            return False
        
        # Test basic query
        session = db_manager.get_session()
        try:
            count = session.query(UserProfile).count()
            print(f"✅ User count: {count}")
            return True
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Database debug failed: {e}")
        return False

def debug_redis():
    """Debug Redis connection"""
    print("🔍 Debugging Redis...")
    
    try:
        from app.core.cache import get_redis_client
        
        redis_client = get_redis_client()
        if redis_client:
            # Test Redis operation
            redis_client.set("debug_test", "working")
            result = redis_client.get("debug_test")
            if result:
                print("✅ Redis connection working")
                return True
            else:
                print("❌ Redis operations failed")
                return False
        else:
            print("⚠️ Redis not configured (this is OK)")
            return True
            
    except Exception as e:
        print(f"❌ Redis debug failed: {e}")
        return False

def debug_auth_manager():
    """Debug authentication manager"""
    print("🔍 Debugging Auth Manager...")
    
    try:
        from app.core.auth import auth_manager
        
        # Test password hashing
        test_password = "TestPassword123!"
        hashed = auth_manager.hash_password(test_password)
        
        if auth_manager.verify_password(test_password, hashed):
            print("✅ Password hashing/verification working")
        else:
            print("❌ Password verification failed")
            return False
        
        # Test token creation
        token = auth_manager.create_access_token("test_user", "test@example.com")
        if token:
            print("✅ Token creation working")
            
            # Test token verification
            payload = auth_manager.verify_token(token)
            if payload.get("user_id") == "test_user":
                print("✅ Token verification working")
                return True
            else:
                print("❌ Token verification failed")
                return False
        else:
            print("❌ Token creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Auth manager debug failed: {e}")
        return False

def debug_agents():
    """Debug AI agents"""
    print("🔍 Debugging AI Agents...")
    
    try:
        from app.agents.base import BaseAgent
        
        # Test base agent
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__("test_agent", "Test Agent")
            
            async def process_request(self, request_data, context):
                return {"status": "success", "message": "Test agent working"}
        
        agent = TestAgent()
        print(f"✅ Base agent created: {agent.agent_id}")
        
        # Test agent orchestrator
        from app.core.orchestrator import orchestrator
        print(f"✅ Orchestrator available with {len(orchestrator.agents)} agents")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent debug failed: {e}")
        return False

def debug_watsonx():
    """Debug WatsonX integration"""
    print("🔍 Debugging WatsonX Integration...")
    
    try:
        from app.integrations.watsonx import WatsonXClient
        from app.core.config import settings
        
        if settings.watsonx_api_key:
            print("✅ WatsonX API key configured")
            # Note: Don't actually test API calls in debug to avoid quota usage
            print("⚠️ Skipping actual API test to preserve quota")
            return True
        else:
            print("⚠️ WatsonX API key not configured (using fallbacks)")
            return True
            
    except Exception as e:
        print(f"❌ WatsonX debug failed: {e}")
        return False

def run_component_debug():
    """Run all component debugging"""
    print("🔍 Starting Component-Specific Debugging...\n")
    
    components = [
        ("Database", debug_database),
        ("Redis", debug_redis),
        ("Auth Manager", debug_auth_manager),
        ("AI Agents", debug_agents),
        ("WatsonX", debug_watsonx),
    ]
    
    results = {}
    
    for name, debug_func in components:
        print(f"\n{'='*40}")
        try:
            result = debug_func()
            results[name] = result
        except Exception as e:
            print(f"❌ {name} debug crashed: {e}")
            results[name] = False
        print(f"{'='*40}")
    
    # Summary
    print(f"\n{'='*50}")
    print("COMPONENT DEBUG SUMMARY")
    print(f"{'='*50}")
    
    for name, result in results.items():
        status = "✅ WORKING" if result else "❌ ISSUES"
        print(f"{status}: {name}")
    
    working = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\nOverall: {working}/{total} components working")

if __name__ == "__main__":
    run_component_debug()