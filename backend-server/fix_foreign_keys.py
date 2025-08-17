#!/usr/bin/env python3
"""Fix foreign key references from users to user_profiles"""

import os
import re

def fix_foreign_keys():
    model_files = [
        'app/models/analytics.py',
        'app/models/career_strategy.py'
    ]
    
    for file_path in model_files:
        if os.path.exists(file_path):
            print(f"Fixing {file_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Replace foreign key references
            content = re.sub(r'ForeignKey\("users\.user_id"\)', 'ForeignKey("user_profiles.user_id")', content)
            content = re.sub(r'ForeignKey\("users\.id"\)', 'ForeignKey("user_profiles.user_id")', content)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Fixed {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

if __name__ == "__main__":
    fix_foreign_keys()
    print("✅ All foreign key references fixed!")