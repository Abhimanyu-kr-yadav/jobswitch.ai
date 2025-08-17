#!/usr/bin/env python3
"""Fix model files to use shared Base"""

import os
import re

def fix_model_bases():
    model_files = [
        'app/models/resume.py',
        'app/models/networking.py', 
        'app/models/job.py',
        'app/models/career_strategy.py',
        'app/models/agent.py'
    ]
    
    for file_path in model_files:
        if os.path.exists(file_path):
            print(f"Fixing {file_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Remove the declarative_base import and Base definition
            content = re.sub(r'from sqlalchemy\.ext\.declarative import declarative_base\n', '', content)
            content = re.sub(r'Base = declarative_base\(\)\n', '', content)
            
            # Add import for shared base
            if 'from .base import Base' not in content:
                # Find the last import line and add our import after it
                lines = content.split('\n')
                last_import_idx = -1
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        last_import_idx = i
                
                if last_import_idx >= 0:
                    lines.insert(last_import_idx + 1, '')
                    lines.insert(last_import_idx + 2, 'from .base import Base')
                    content = '\n'.join(lines)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Fixed {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

if __name__ == "__main__":
    fix_model_bases()
    print("✅ All model files updated to use shared Base!")