# Legacy main.py - redirects to new application structure
# This file is kept for backward compatibility

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import the new main application
from app.main import app

# Export the app for uvicorn
__all__ = ['app']
