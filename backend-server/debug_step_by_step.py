#!/usr/bin/env python3
"""Step-by-step debugging script"""

import sys
import os
import pdb
import requests
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_authentication_flow():
    """Debug authentication step by step"""
    print("🔍 Starting step-by-step authentication debugging")
    
    # Step 1: Test server connection
    print("\n=== STEP 1: Testing server connection ===")
    breakpoint()  # Pause here to examine
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        print(f"Health response: {response.json()}")
    except Exception as e:
        print(f"Server connection failed: {e}")
        return False
    
    # Step 2: Prepare registration data
    print("\n=== STEP 2: Preparing registration data ===")
    breakpoint()  # Pause here to examine data
    
    reg_data = {
        "email": "debug_step@example.com",
        "password": "TestPass123!",
        "first_name": "Debug",
        "last_name": "Step"
    }
    print(f"Registration data: {json.dumps(reg_data, indent=2)}")
    
    # Step 3: Send registration request
    print("\n=== STEP 3: Sending registration request ===")
    breakpoint()  # Pause before sending request
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/register",
            json=reg_data,
            timeout=10
        )
        print(f"Registration status: {response.status_code}")
        print(f"Registration response: {response.text}")
        
        if response.status_code >= 400:
            print("❌ Registration failed, debugging response...")
            breakpoint()  # Pause to examine error
            return False
            
    except Exception as e:
        print(f"Registration request failed: {e}")
        breakpoint()  # Pause to examine exception
        return False
    
    # Step 4: Test login
    print("\n=== STEP 4: Testing login ===")
    breakpoint()  # Pause before login
    
    login_data = {
        "email": reg_data["email"],
        "password": reg_data["password"]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        print(f"Login status: {response.status_code}")
        print(f"Login response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Authentication flow completed successfully!")
            return True
        else:
            print("❌ Login failed")
            breakpoint()  # Pause to examine login failure
            return False
            
    except Exception as e:
        print(f"Login request failed: {e}")
        breakpoint()  # Pause to examine exception
        return False

def debug_database_models():
    """Debug database models step by step"""
    print("🔍 Starting step-by-step database model debugging")
    
    # Step 1: Import models
    print("\n=== STEP 1: Importing models ===")
    breakpoint()
    
    try:
        from app.models.base import Base
        from app.models.user import UserProfile
        from app.models.analytics import JobSearchMetrics
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        breakpoint()
        return False
    
    # Step 2: Create in-memory database
    print("\n=== STEP 2: Creating test database ===")
    breakpoint()
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine("sqlite:///:memory:", echo=True)
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        print("✅ Test database created")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        breakpoint()
        return False
    
    # Step 3: Create test user
    print("\n=== STEP 3: Creating test user ===")
    breakpoint()
    
    try:
        user = UserProfile(
            user_id="debug_user_123",
            email="debug@example.com",
            password_hash="hashed_password",
            first_name="Debug",
            last_name="User"
        )
        
        session.add(user)
        session.commit()
        print("✅ Test user created successfully")
        
        # Step 4: Query user
        print("\n=== STEP 4: Querying user ===")
        breakpoint()
        
        queried_user = session.query(UserProfile).filter(
            UserProfile.email == "debug@example.com"
        ).first()
        
        if queried_user:
            print(f"✅ User found: {queried_user.full_name}")
            return True
        else:
            print("❌ User not found")
            breakpoint()
            return False
            
    except Exception as e:
        print(f"❌ User creation/query failed: {e}")
        breakpoint()
        return False
    finally:
        session.close()

def debug_specific_component(component_name):
    """Debug a specific component"""
    print(f"🔍 Debugging component: {component_name}")
    
    if component_name == "auth":
        return debug_authentication_flow()
    elif component_name == "models":
        return debug_database_models()
    else:
        print(f"Unknown component: {component_name}")
        print("Available components: auth, models")
        return False

if __name__ == "__main__":
    print("🔍 Step-by-Step Debugger")
    print("=" * 50)
    print("This script will pause at each step for debugging")
    print("PDB Commands:")
    print("  n - next line")
    print("  s - step into function")
    print("  c - continue execution")
    print("  l - list current code")
    print("  p <var> - print variable")
    print("  pp <var> - pretty print variable")
    print("  q - quit debugger")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        component = sys.argv[1]
        debug_specific_component(component)
    else:
        print("Usage: python debug_step_by_step.py [auth|models]")
        print("Or run without arguments for interactive selection")
        
        print("\nSelect component to debug:")
        print("1. Authentication flow")
        print("2. Database models")
        
        choice = input("Enter choice (1-2): ")
        
        if choice == "1":
            debug_authentication_flow()
        elif choice == "2":
            debug_database_models()
        else:
            print("Invalid choice")