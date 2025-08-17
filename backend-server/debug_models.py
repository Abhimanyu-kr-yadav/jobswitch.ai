#!/usr/bin/env python3
"""Debug script to identify model relationship issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_individual_models():
    """Test each model individually to identify the problematic one"""
    
    try:
        print("Testing base model...")
        from app.models.base import Base
        print("✅ Base model OK")
        
        print("Testing user model...")
        from app.models.user import UserProfile
        print("✅ User model OK")
        
        print("Testing analytics models...")
        from app.models.analytics import UserActivity, JobSearchMetrics, ABTestParticipant, UserReport
        print("✅ Analytics models OK")
        
        print("Testing career strategy models...")
        from app.models.career_strategy import CareerRoadmap, CareerGoal, CareerMilestone
        print("✅ Career strategy models OK")
        
        print("Testing job models...")
        from app.models.job import Job
        print("✅ Job models OK")
        
        print("Testing agent models...")
        from app.models.agent import AgentTask
        print("✅ Agent models OK")
        
        print("Testing resume models...")
        from app.models.resume import Resume
        print("✅ Resume models OK")
        
        print("Testing networking models...")
        from app.models.networking import Contact
        print("✅ Networking models OK")
        
        print("\n🎉 All individual model imports successful!")
        
        # Now test creating the database schema
        print("\nTesting database schema creation...")
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///:memory:", echo=False)
        
        Base.metadata.create_all(engine)
        print("✅ Database schema created successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_individual_models()
    if not success:
        sys.exit(1)