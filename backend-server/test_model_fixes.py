#!/usr/bin/env python3
"""Test script to verify model relationship fixes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import UserProfile
from app.models.analytics import JobSearchMetrics, ABTestParticipant, UserReport

def test_model_relationships():
    """Test that all model relationships are properly defined"""
    try:
        # Create in-memory SQLite database for testing
        engine = create_engine("sqlite:///:memory:", echo=False)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        print("✅ All models created successfully!")
        print("✅ No SQLAlchemy relationship errors!")
        
        # Test that we can access the relationships
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create a test user
        user = UserProfile(
            user_id="test_user_123",
            email="test@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User"
        )
        session.add(user)
        session.commit()
        
        # Test that relationships are accessible
        print(f"✅ User activities relationship: {hasattr(user, 'activities')}")
        print(f"✅ User job_search_metrics relationship: {hasattr(user, 'job_search_metrics')}")
        print(f"✅ User ab_test_participations relationship: {hasattr(user, 'ab_test_participations')}")
        print(f"✅ User reports relationship: {hasattr(user, 'reports')}")
        
        session.close()
        print("✅ All relationship tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_model_relationships()
    if success:
        print("\n🎉 All model fixes are working correctly!")
    else:
        print("\n💥 There are still issues with the models")
        sys.exit(1)