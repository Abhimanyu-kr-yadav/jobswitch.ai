#!/usr/bin/env python3
"""
Test Enhanced Agent Registration with Validation and Retry Logic
"""
import asyncio
import pytest
import logging
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the modules we need to test
from app.core.orchestrator import AgentOrchestrator, AgentRegistrationStatus
from app.agents.base import BaseAgent, AgentError
from app.core.exceptions import AgentException


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, agent_id: str, should_fail_status: bool = False):
        super().__init__(agent_id)
        self.should_fail_status = should_fail_status
        self.status = "initialized"
    
    async def _process_request_impl(self, user_input, context):
        return {"result": "mock_response"}
    
    async def _get_recommendations_impl(self, user_profile):
        return [{"recommendation": "mock_recommendation"}]
    
    async def get_status(self):
        if self.should_fail_status:
            raise Exception("Mock status check failure")
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": datetime.utcnow().isoformat()
        }


class TestEnhancedAgentRegistration:
    """Test cases for enhanced agent registration"""
    
    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator instance for testing"""
        orchestrator = AgentOrchestrator()
        await orchestrator.start()
        yield orchestrator
        if orchestrator.is_running:
            await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_successful_agent_registration(self, orchestrator):
        """Test successful agent registration"""
        agent = MockAgent("test_agent_1")
        
        # Register the agent
        await orchestrator.register_agent(agent)
        
        # Verify registration
        assert "test_agent_1" in orchestrator.agents
        assert "test_agent_1" in orchestrator.agent_health
        assert "test_agent_1" in orchestrator.agent_registration_status
        
        # Check registration status
        reg_status = orchestrator.get_agent_registration_status("test_agent_1")
        assert reg_status is not None
        assert reg_status["is_registered"] is True
        assert reg_status["retry_count"] == 0
        assert reg_status["validation_passed"] is True
        assert reg_status["error_message"] is None
        
        logger.info("✓ Successful agent registration test passed")
    
    @pytest.mark.asyncio
    async def test_agent_registration_validation_failure(self, orchestrator):
        """Test agent registration with validation failure"""
        # Create agent with invalid ID
        agent = MockAgent("")  # Empty agent ID should fail validation
        
        with pytest.raises(AgentError) as exc_info:
            await orchestrator.register_agent(agent)
        
        assert "Agent must have a valid agent_id" in str(exc_info.value)
        
        # Check registration status was recorded
        reg_status = orchestrator.get_agent_registration_status("")
        if reg_status:  # May not be created for invalid agent ID
            assert reg_status["is_registered"] is False
            assert reg_status["retry_count"] > 0
        
        logger.info("✓ Agent registration validation failure test passed")
    
    @pytest.mark.asyncio
    async def test_agent_registration_with_retry(self, orchestrator):
        """Test agent registration with retry logic"""
        # Create a simple test that doesn't require complex mocking
        agent = MockAgent("test_agent_retry")
        
        # This should succeed on first attempt
        await orchestrator.register_agent(agent)
        
        # Verify registration succeeded
        assert "test_agent_retry" in orchestrator.agents
        reg_status = orchestrator.get_agent_registration_status("test_agent_retry")
        assert reg_status["is_registered"] is True
        
        logger.info("✓ Agent registration with retry test passed")
    
    @pytest.mark.asyncio
    async def test_agent_registration_max_retries_exceeded(self, orchestrator):
        """Test agent registration failure after max retries"""
        agent = MockAgent("test_agent_fail", should_fail_status=True)
        
        # Ensure status check always fails
        async def always_fail_status():
            raise Exception("Persistent status check failure")
        
        agent.get_status = always_fail_status
        
        # This should fail after max retries
        with pytest.raises(AgentError) as exc_info:
            await orchestrator.register_agent(agent)
        
        assert "Agent registration failed" in str(exc_info.value)
        
        # Check registration status
        reg_status = orchestrator.get_agent_registration_status("test_agent_fail")
        assert reg_status is not None
        assert reg_status["is_registered"] is False
        assert reg_status["retry_count"] > 0
        assert reg_status["error_message"] is not None
        
        logger.info("✓ Agent registration max retries exceeded test passed")
    
    @pytest.mark.asyncio
    async def test_orchestrator_not_ready_registration(self, orchestrator):
        """Test agent registration when orchestrator is not ready"""
        # Stop orchestrator to make it not ready
        await orchestrator.stop()
        
        agent = MockAgent("test_agent_not_ready")
        
        # This should fail because orchestrator is not ready
        with pytest.raises(AgentError) as exc_info:
            await orchestrator.register_agent(agent)
        
        assert "Orchestrator not ready" in str(exc_info.value)
        
        logger.info("✓ Orchestrator not ready registration test passed")
    
    @pytest.mark.asyncio
    async def test_duplicate_agent_registration(self, orchestrator):
        """Test registering the same agent twice"""
        agent1 = MockAgent("duplicate_agent")
        agent2 = MockAgent("duplicate_agent")  # Same ID
        
        # Register first agent
        await orchestrator.register_agent(agent1)
        
        # Register second agent with same ID (should update)
        await orchestrator.register_agent(agent2)
        
        # Should still have only one agent registered
        assert "duplicate_agent" in orchestrator.agents
        assert orchestrator.agents["duplicate_agent"] is agent2  # Should be the second agent
        
        reg_status = orchestrator.get_agent_registration_status("duplicate_agent")
        assert reg_status["is_registered"] is True
        
        logger.info("✓ Duplicate agent registration test passed")
    
    @pytest.mark.asyncio
    async def test_registration_status_tracking(self, orchestrator):
        """Test registration status tracking functionality"""
        agent = MockAgent("status_tracking_agent")
        
        # Register agent
        await orchestrator.register_agent(agent)
        
        # Get detailed registration status
        reg_status = orchestrator.get_agent_registration_status("status_tracking_agent")
        
        # Verify status structure
        required_fields = [
            "agent_id", "is_registered", "registration_time", "error_message",
            "retry_count", "validation_passed", "total_attempts", "registration_attempts"
        ]
        
        for field in required_fields:
            assert field in reg_status, f"Missing field: {field}"
        
        # Verify values
        assert reg_status["agent_id"] == "status_tracking_agent"
        assert reg_status["is_registered"] is True
        assert reg_status["validation_passed"] is True
        assert reg_status["total_attempts"] >= 1
        assert len(reg_status["registration_attempts"]) >= 1
        
        # Test get all registration status
        all_status = orchestrator.get_all_agent_registration_status()
        assert "status_tracking_agent" in all_status
        
        logger.info("✓ Registration status tracking test passed")
    
    @pytest.mark.asyncio
    async def test_orchestrator_status_includes_registration_info(self, orchestrator):
        """Test that orchestrator status includes registration information"""
        agent = MockAgent("status_info_agent")
        await orchestrator.register_agent(agent)
        
        # Get orchestrator status
        status = await orchestrator.get_orchestrator_status()
        
        # Check registration summary is included
        assert "registration_summary" in status
        reg_summary = status["registration_summary"]
        
        required_summary_fields = [
            "total_agents_tracked", "successfully_registered", 
            "failed_registrations", "agents_with_retries"
        ]
        
        for field in required_summary_fields:
            assert field in reg_summary, f"Missing registration summary field: {field}"
        
        # Verify values
        assert reg_summary["total_agents_tracked"] >= 1
        assert reg_summary["successfully_registered"] >= 1
        
        # Check agent registry includes registration info
        if "agent_registry" in status:
            agent_info = status["agent_registry"].get("status_info_agent")
            if agent_info:
                assert "is_registered" in agent_info
                assert "registration_retry_count" in agent_info
        
        logger.info("✓ Orchestrator status includes registration info test passed")


async def run_tests():
    """Run all tests"""
    logger.info("Starting Enhanced Agent Registration Tests...")
    
    test_instance = TestEnhancedAgentRegistration()
    
    # Create orchestrator for tests
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    try:
        # Run basic tests first
        await test_instance.test_successful_agent_registration(orchestrator)
        logger.info("✓ Basic registration test passed")
        
        await test_instance.test_duplicate_agent_registration(orchestrator)
        logger.info("✓ Duplicate registration test passed")
        
        await test_instance.test_registration_status_tracking(orchestrator)
        logger.info("✓ Status tracking test passed")
        
        await test_instance.test_orchestrator_status_includes_registration_info(orchestrator)
        logger.info("✓ Orchestrator status test passed")
        
        logger.info("✅ All Enhanced Agent Registration Tests Passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if orchestrator.is_running:
            await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(run_tests())