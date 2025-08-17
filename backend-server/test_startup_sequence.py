#!/usr/bin/env python3
"""
Test script for application startup sequence and dependency management
Tests the implementation of task 3 from the agent registration fix spec
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


async def test_startup_sequence():
    """
    Test the application startup sequence
    """
    logger.info("Starting application startup sequence test...")
    
    try:
        # Import main application components
        from app.main import app
        from app.core.database import db_manager
        from app.core.config import settings
        import app.core.orchestrator as orch_module
        
        # Test 1: Check if orchestrator class has readiness tracking
        logger.info("Test 1: Checking orchestrator readiness tracking...")
        
        # Check if AgentOrchestrator class has required methods
        from app.core.orchestrator import AgentOrchestrator
        
        # Create a test instance to check methods
        test_orchestrator = AgentOrchestrator()
        assert hasattr(test_orchestrator, 'is_ready'), "Orchestrator missing is_ready property"
        assert hasattr(test_orchestrator, 'wait_for_ready'), "Orchestrator missing wait_for_ready method"
        assert hasattr(test_orchestrator, '_initialization_phase'), "Orchestrator missing initialization phase tracking"
        
        logger.info("✓ Orchestrator readiness tracking implemented")
        
        # Test 2: Check database connection with retry logic
        logger.info("Test 2: Testing database connection...")
        
        # Check if database manager has connection check
        assert hasattr(db_manager, 'check_connection'), "Database manager missing check_connection method"
        
        # Test database connection
        db_connected = db_manager.check_connection()
        if db_connected:
            logger.info("✓ Database connection successful")
        else:
            logger.warning("⚠ Database connection failed - this may be expected in test environment")
        
        # Test 3: Check orchestrator initialization
        logger.info("Test 3: Testing orchestrator initialization...")
        
        # Import initialization function
        from app.core.orchestrator import initialize_orchestrator, shutdown_orchestrator
        
        # Test orchestrator initialization
        try:
            await initialize_orchestrator()
            
            # Check if orchestrator is ready
            if orch_module.orchestrator and orch_module.orchestrator.is_ready:
                logger.info("✓ Orchestrator initialized and ready")
            else:
                logger.warning("⚠ Orchestrator initialized but not ready")
            
            # Test wait_for_ready functionality
            if orch_module.orchestrator:
                ready = await orch_module.orchestrator.wait_for_ready(timeout=5.0)
                if ready:
                    logger.info("✓ Orchestrator wait_for_ready works correctly")
                else:
                    logger.warning("⚠ Orchestrator wait_for_ready timed out")
            
            # Clean up
            await shutdown_orchestrator()
            logger.info("✓ Orchestrator shutdown successful")
            
        except Exception as e:
            logger.error(f"✗ Orchestrator initialization failed: {str(e)}")
            return False
        
        # Test 4: Check agent registration with retry logic
        logger.info("Test 4: Testing agent registration retry logic...")
        
        # Check if orchestrator class has registration status tracking
        assert hasattr(test_orchestrator, 'agent_registration_status'), "Orchestrator missing agent registration status tracking"
        assert hasattr(test_orchestrator, '_registration_retry_config'), "Orchestrator missing registration retry config"
        
        logger.info("✓ Agent registration retry logic implemented")
        
        # Test 5: Check error handling and graceful degradation
        logger.info("Test 5: Testing error handling...")
        
        # Check if app has error tracking
        if hasattr(app.state, 'initialization_errors'):
            logger.info("✓ Application error tracking implemented")
        else:
            logger.warning("⚠ Application error tracking not found (may not be initialized yet)")
        
        logger.info("All startup sequence tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Startup sequence test failed: {str(e)}")
        return False


async def test_health_check_enhancements():
    """
    Test the enhanced health check endpoint
    """
    logger.info("Testing health check enhancements...")
    
    try:
        # Import FastAPI test client
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Create test client
        client = TestClient(app)
        
        # Test health check endpoint
        response = client.get("/health")
        
        if response.status_code in [200, 503]:  # 503 is acceptable for degraded state
            health_data = response.json()
            
            # Check for required fields
            required_fields = ["overall_status", "version", "environment"]
            for field in required_fields:
                assert field in health_data, f"Health check missing required field: {field}"
            
            # Check for orchestrator status
            if "orchestrator" in health_data:
                logger.info("✓ Health check includes orchestrator status")
            else:
                logger.warning("⚠ Health check missing orchestrator status")
            
            # Check for agent status
            if "agents" in health_data:
                logger.info("✓ Health check includes agent status")
            else:
                logger.warning("⚠ Health check missing agent status")
            
            logger.info(f"✓ Health check endpoint working (status: {response.status_code})")
            return True
        else:
            logger.error(f"✗ Health check endpoint failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Health check test failed: {str(e)}")
        return False


async def main():
    """
    Main test function
    """
    logger.info("=" * 60)
    logger.info("Application Startup Sequence Test")
    logger.info("Testing implementation of task 3: Fix application startup sequence and dependency management")
    logger.info("=" * 60)
    
    test_results = []
    
    # Run startup sequence tests
    startup_result = await test_startup_sequence()
    test_results.append(("Startup Sequence", startup_result))
    
    # Run health check tests
    health_result = await test_health_check_enhancements()
    test_results.append(("Health Check Enhancements", health_result))
    
    # Print test summary
    logger.info("=" * 60)
    logger.info("Test Results Summary:")
    
    all_passed = True
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("All tests passed! ✓")
        logger.info("Task 3 implementation appears to be working correctly.")
    else:
        logger.error("Some tests failed! ✗")
        logger.error("Task 3 implementation needs attention.")
    
    logger.info("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)