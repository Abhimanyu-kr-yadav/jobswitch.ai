#!/usr/bin/env python3
"""Simple test to verify model imports work"""

import sys
import os

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that models can be imported without errors"""
    try:
        print("Testing model imports...")
        
        # Test base model import
        from app.models.base import Base
        print("✅ Base model imported successfully")
        
        # Test user model import
        from app.models.user import UserProfile
        print("✅ UserProfile model imported successfully")
        
        # Test analytics model import
        from app.models.analytics import JobSearchMetrics, ABTestParticipant, UserReport
        print("✅ Analytics models imported successfully")
        
        print("\n🎉 All model imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_model_imports()
    if not success:
        sys.exit(1)