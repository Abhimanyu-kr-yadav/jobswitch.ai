#!/usr/bin/env python3
"""Script to recreate the database with the correct schema"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.models.base import Base
from app.core.config import settings

# Import all models to ensure they're registered
import app.models.user
import app.models.job
import app.models.agent
import app.models.analytics
import app.models.resume
import app.models.networking
import app.models.career_strategy

def recreate_database():
    """Recreate the database with the current schema"""
    try:
        print("Recreating database with current schema...")
        
        # Create engine
        engine = create_engine(settings.database_url, echo=True)
        
        print("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("Creating all tables with current schema...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database recreated successfully!")
        
        # Test that we can connect and query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            print(f"Created tables: {tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error recreating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = recreate_database()
    if not success:
        sys.exit(1)