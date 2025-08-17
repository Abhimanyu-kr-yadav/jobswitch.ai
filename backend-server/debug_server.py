#!/usr/bin/env python3
"""Debug-enabled FastAPI server with breakpoint support"""

import sys
import os
import pdb
import uvicorn
from pathlib import Path

# Add the backend-server directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your main app
from app.main import app

def debug_auth_endpoint():
    """Add debugging to auth endpoints"""
    from app.api import auth
    
    # Monkey patch the register function to add debugging
    original_register = auth.register_user
    
    async def debug_register_user(*args, **kwargs):
        print("🔍 DEBUG: Starting user registration")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        
        # Set breakpoint here
        breakpoint()
        
        # Call original function
        result = await original_register(*args, **kwargs)
        
        print(f"🔍 DEBUG: Registration result: {result}")
        return result
    
    # Replace the original function
    auth.register_user = debug_register_user
    print("✅ Debug breakpoint added to registration endpoint")

def debug_database_operations():
    """Add debugging to database operations"""
    from app.core import database
    
    original_get_database = database.get_database
    
    def debug_get_database():
        print("🔍 DEBUG: Getting database session")
        breakpoint()  # Debug database connection
        return original_get_database()
    
    database.get_database = debug_get_database
    print("✅ Debug breakpoint added to database operations")

def debug_model_operations():
    """Add debugging to model operations"""
    from app.models.user import UserProfile
    
    # Add debugging to UserProfile creation
    original_init = UserProfile.__init__
    
    def debug_init(self, *args, **kwargs):
        print("🔍 DEBUG: Creating UserProfile")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        breakpoint()  # Debug model creation
        return original_init(self, *args, **kwargs)
    
    UserProfile.__init__ = debug_init
    print("✅ Debug breakpoint added to UserProfile creation")

if __name__ == "__main__":
    print("🔍 Starting JobSwitch.ai in DEBUG mode...")
    print("Breakpoints will be triggered during execution")
    print("Use these pdb commands:")
    print("  n (next line)")
    print("  s (step into)")
    print("  c (continue)")
    print("  l (list code)")
    print("  p <variable> (print variable)")
    print("  pp <variable> (pretty print)")
    print("  q (quit)")
    print("="*50)
    
    # Add debug breakpoints to key components
    debug_auth_endpoint()
    debug_database_operations()
    debug_model_operations()
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for debugging
        log_level="debug"
    )