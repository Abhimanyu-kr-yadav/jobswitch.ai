#!/usr/bin/env python3
"""
Minimal test to isolate import issues
"""
import sys
import os

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_api_imports():
    """Test API imports specifically"""
    try:
        print("Testing analytics API import...")
        from app.api.analytics import router as analytics_router
        print("✅ Analytics API imported successfully")
        
        print("Testing A/B testing API import...")
        from app.api.ab_testing import router as ab_testing_router
        print("✅ A/B testing API imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ API import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_imports()
    if success:
        print("🎉 All API imports successful!")
    else:
        print("❌ API import test failed")
    sys.exit(0 if success else 1)