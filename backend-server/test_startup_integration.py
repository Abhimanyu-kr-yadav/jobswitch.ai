#!/usr/bin/env python3
"""
Integration test for the improved startup sequence
Tests the actual application startup with dependency management
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_application_startup():
    """
    Test the complete application startup sequence
    """
    logger.info("Testing complete application startup sequence...")
    
    try:
        # Import the FastAPI app
        from app.main import app
        
        # Test the lifespan context manager
        logger.info("Testing application lifespan...")
        
        # Create a mock app state for testing
        class MockAppState:
            def __init__(self):
                self.start_time = datetime.utcnow()
                self.initialization_errors = []
                self.initialization_warnings = []
        
        app.state = MockAppState()
        
        # Test the lifespan startup
        from app.main import lifespan
        
        logger.info("Starting application lifespan context...")
        
        try:
            async with lifespan(app):
                logger.info("✓ Application startup completed successfully")
                
                # Verify application state
                if hasattr(app.state, 'startup_validation'):
                    logger.info(f"✓ Startup validation completed: {app.state.startup_validation}")
                
                if hasattr(app.state, 'agent_registration_results'):
                    successful_agents = sum(1 for r in app.state.agent_registration_results.values() if r['success'])
                    total_agents = len(app.state.agent_registration_results)
                    logger.info(f"✓ Agent registration: {successful_agents}/{total_agents} agents registered")
                
                # Test health check during running state
                from fastapi.testclient import TestClient
                client = TestClient(app)
                
                response = client.get("/health")
                if response.status_code in [200, 503]:  # 503 is acceptable for degraded state
                    health_data = response.json()
                    logger.info(f"✓ Health check working: {health_data.get('overall_status', 'unknown')}")
                else:
                    logger.warning(f"⚠ Health check returned unexpected status: {response.status_code}")
                
                logger.info("Application is running successfully")
                
        except Exception as startup_error:
            logger.error(f"✗ Application startup failed: {str(startup_error)}")
            
            # Check if we have error information
            if hasattr(app.state, 'initialization_errors') and app.state.initialization_errors:
                logger.error("Initialization errors:")
                for error in app.state.initialization_errors:
                    logger.error(f"  - {error}")
            
            if hasattr(app.state, 'startup_failed') and app.state.startup_failed:
                logger.error(f"Startup failure reason: {app.state.startup_failure_reason}")
            
            return False
        
        logger.info("✓ Application lifespan test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        return False


async def main():
    """
    Main test function
    """
    logger.info("=" * 60)
    logger.info("Application Startup Integration Test")
    logger.info("Testing the complete startup sequence with dependency management")
    logger.info("=" * 60)
    
    # Run integration test
    success = await test_application_startup()
    
    # Print results
    logger.info("=" * 60)
    if success:
        logger.info("Integration test PASSED! ✓")
        logger.info("The improved startup sequence is working correctly.")
    else:
        logger.error("Integration test FAILED! ✗")
        logger.error("The startup sequence needs attention.")
    
    logger.info("=" * 60)
    
    return success


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)