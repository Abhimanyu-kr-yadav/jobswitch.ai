#!/usr/bin/env python3
"""
Script to fix career_strategy.py by adding agent dependency to functions that need it
"""

import re

# Read the file
with open('app/api/career_strategy.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Functions that need the agent dependency (based on the grep search)
functions_needing_agent = [
    'generate_career_roadmap',
    'create_career_goals', 
    'track_progress',
    'analyze_market_trends',
    'get_career_recommendations'
]

# For each function, add the agent dependency if it's not already there
for func_name in functions_needing_agent:
    # Pattern to match the function signature
    pattern = rf'(async def {func_name}\([^)]*)\):'
    
    def add_agent_dependency(match):
        params = match.group(1)
        if 'career_agent' not in params:
            # Add the agent dependency
            return f"{params},\n    career_agent: CareerStrategyAgent = Depends(get_career_strategy_agent)\n):"
        return match.group(0)
    
    content = re.sub(pattern, add_agent_dependency, content, flags=re.MULTILINE | re.DOTALL)

# Write the file back
with open('app/api/career_strategy.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed career_strategy.py - added agent dependencies")