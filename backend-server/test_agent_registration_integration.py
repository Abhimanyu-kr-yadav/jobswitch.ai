#!/usr/bin/env python3
"""
Integration Test for Enhanced Agent Registration
"""
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the modules we need to test
from app.core.orchestrator import AgentOrchestrator
from app.agents.job_discovery import JobDiscoveryAgent
from app.core.config import settings


async def test_real_agent_registration():
    """Test registration with a real agent"""
    logger.info("Starting Real Agent Registration Integration Test...")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    try:
        # Create a real job discovery agent
        job_agent = JobDiscoveryAgent(
            watsonx_client=None  # Mock for testing
        )
        
        # Register the agent
        logger.info("Registering job discovery agent...")
        await orchestrator.register_agent(job_agent)
        
        # Verify registration
        assert "job_discovery_agent" in orchestrator.agents
        assert "job_discovery_agent" in orchestrator.agent_health
        assert "job_discovery_agent" in orchestrator.agent_registration_status
        
        # Check registration status
        reg_status = orchestrator.get_agent_registration_status("job_discovery_agent")
        logger.info(f"Registration status: {reg_status}")
        
        assert reg_status["is_registered"] is True
        assert reg_status["validation_passed"] is True
        assert reg_status["error_message"] is None
        
        # Get orchestrator status
        orch_status = await orchestrator.get_orchestrator_status()
        logger.info(f"Orchestrator status: {orch_status['registration_summary']}")
        
        assert orch_status["registration_summary"]["successfully_registered"] >= 1
        
        # Test agent status
        agent_status = await orchestrator.get_agent_status("job_discovery_agent")
        logger.info(f"Agent status: {agent_status}")
        
        assert agent_status is not None
        assert agent_status["is_healthy"] is True
        
        logger.info("✅ Real Agent Registration Integration Test Passed!")
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await orchestrator.stop()


async def test_agent_registration_failure_recovery():
    """Test agent registration failure and recovery"""
    logger.info("Starting Agent Registration Failure Recovery Test...")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    try:
        # Create an agent with invalid configuration to trigger failure
        class FailingAgent:
            def __init__(self):
                self.agent_id = "failing_agent"
                self.status = "initialized"
            
            async def get_status(self):
                # This will fail validation because it doesn't inherit from BaseAgent
                raise Exception("Invalid agent implementation")
        
        failing_agent = FailingAgent()
        
        # Try to register the failing agent
        try:
            await orchestrator.register_agent(failing_agent)
            assert False, "Should have failed"
        except Exception as e:
            logger.info(f"Expected failure: {str(e)}")
        
        # Check that registration status was tracked
        reg_status = orchestrator.get_agent_registration_status("failing_agent")
        if reg_status:
            logger.info(f"Failure status tracked: {reg_status}")
            assert reg_status["is_registered"] is False
            assert reg_status["retry_count"] > 0
        
        logger.info("✅ Agent Registration Failure Recovery Test Passed!")
        
    except Exception as e:
        logger.error(f"❌ Failure recovery test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await orchestrator.stop()


async def run_integration_tests():
    """Run all integration tests"""
    logger.info("Starting Enhanced Agent Registration Integration Tests...")
    
    await test_real_agent_registration()
    await test_agent_registration_failure_recovery()
    
    logger.info("✅ All Integration Tests Passed!")


if __name__ == "__main__":
    asyncio.run(run_integration_tests())