"""
Minimal test to isolate the class definition issue
"""

# Test 1: Can we define a simple class?
class TestClass:
    def __init__(self):
        self.name = "test"

print("Simple class defined:", TestClass)

# Test 2: Can we import BaseAgent?
try:
    from app.agents.base import BaseAgent
    print("BaseAgent imported successfully")
    
    # Test 3: Can we inherit from BaseAgent?
    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__("test", None, None)
        
        async def process_request(self, user_input, context):
            return {"success": True}
        
        async def get_recommendations(self, user_profile):
            return []
    
    print("TestAgent defined:", TestAgent)
    
    # Test 4: Can we create an instance?
    agent = TestAgent()
    print("TestAgent instance created:", agent)
    
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()