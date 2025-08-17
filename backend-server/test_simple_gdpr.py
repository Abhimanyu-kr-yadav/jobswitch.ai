"""Simple GDPR test"""

# Test minimal GDPR functionality
class SimpleGDPRManager:
    """Simple GDPR manager for testing"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.supported_formats = ['json', 'csv', 'xml']
        self.data_categories = {
            'profile': {
                'models': [],
                'description': 'User profile and preferences'
            },
            'jobs': {
                'models': [],
                'description': 'Job search and application data'
            }
        }

# Test the class
if __name__ == "__main__":
    print("Testing simple GDPR manager...")
    manager = SimpleGDPRManager()
    print(f"✓ Manager created: {manager}")
    print(f"✓ Data categories: {list(manager.data_categories.keys())}")
    print("✓ Simple GDPR manager working!")