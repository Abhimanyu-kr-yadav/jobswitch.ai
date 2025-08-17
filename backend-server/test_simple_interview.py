"""
Simple test for interview preparation agent
"""

# Test basic class definition
class TestInterviewAgent:
    def __init__(self):
        self.name = "test"
    
    def test_method(self):
        return "working"

# Test the class
agent = TestInterviewAgent()
print(f"Agent name: {agent.name}")
print(f"Test method: {agent.test_method()}")

# Now test importing the actual agent
try:
    from app.agents.interview_preparation import InterviewPreparationAgent
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    
    # Try to debug the issue
    import app.agents.interview_preparation as module
    print(f"Module attributes: {dir(module)}")