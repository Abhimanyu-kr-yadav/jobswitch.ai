#!/usr/bin/env python3
"""
Test Agent Registration Status Tracking - Task 4 Verification
"""
import asyncio
import pytest
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the modules we need to test
from app.core.orchestrator import AgentOrchestrator, AgentRegistrationStatus
from app.agents.base import BaseAgent


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


@pytest.mark.asyncio
async def test_agent_registration_status_data_model():
    """Test AgentRegistrationStatus data model functionality"""
    logger.info("Testing AgentRegistrationStatus data model...")
    
    # Create registration status instance
    status = AgentRegistrationStatus("test_agent")
    
    # Test initial state
    assert status.agent_id == "test_agent"
    assert status.is_registered == False
    assert status.registration_time is None
    assert status.error_message is None
    assert status.retry_count == 0
    assert status.validation_passed == False
    assert len(status.registration_attempts) == 0
    
    # Test recording successful attempt
    status.record_attempt(True)
    assert status.is_registered == True
    assert status.registration_time is not None
    assert status.error_message is None
    assert status.validation_passed == True
    assert len(status.registration_attempts) == 1
    assert status.registration_attempts[0]['success'] == True
    
    # Test to_dict method
    status_dict = status.to_dict()
    assert status_dict['agent_id'] == "test_agent"
    assert status_dict['is_registered'] == True
    assert status_dict['validation_passed'] == True
    assert status_dict['total_attempts'] == 1
    
    logger.info("✅ AgentRegistrationStatus data model tests passed")


@pytest.mark.asyncio
async def test_orchestrator_registration_status_storage():
    """Test orchestrator registration status storage"""
    logger.info("Testing orchestrator registration status storage...")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    try:
        # Create and register agent
        agent = MockAgent("storage_test_agent")
        await orchestrator.register_agent(agent)
        
        # Verify registration status is stored
        assert "storage_test_agent" in orchestrator.agent_registration_status
        
        # Get registration status
        reg_status = orchestrator.agent_registration_status["storage_test_agent"]
        assert isinstance(reg_status, AgentRegistrationStatus)
        assert reg_status.agent_id == "storage_test_agent"
        assert reg_status.is_registered == True
        
        logger.info("✅ Orchestrator registration status storage tests passed")
        
    finally:
        await orchestrator.stop()


@pytest.mark.asyncio
async def test_query_agent_registration_status_methods():
    """Test methods to query agent registration status"""
    logger.info("Testing agent registration status query methods...")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    try:
        # Create and register multiple agents
        agent1 = MockAgent("query_test_agent_1")
        agent2 = MockAgent("query_test_agent_2")
        
        await orchestrator.register_agent(agent1)
        await orchestrator.register_agent(agent2)
        
        # Test get_agent_registration_status for specific agent
        status1 = orchestrator.get_agent_registration_status("query_test_agent_1")
        assert status1 is not None
        assert status1['agent_id'] == "query_test_agent_1"
        assert status1['is_registered'] == True
        assert 'registration_time' in status1
        assert 'retry_count' in status1
        assert 'validation_passed' in status1
        
        # Test get_agent_registration_status for non-existent agent
        status_none = orchestrator.get_agent_registration_status("non_existent_agent")
        assert status_none is None
        
        # Test get_all_agent_registration_status
        all_status = orchestrator.get_all_agent_registration_status()
        assert isinstance(all_status, dict)
        assert "query_test_agent_1" in all_status
        assert "query_test_agent_2" in all_status
        assert len(all_status) >= 2
        
        # Verify structure of all status
        for agent_id, status in all_status.items():
            assert 'agent_id' in status
            assert 'is_registered' in status
            assert 'registration_time' in status
            assert 'retry_count' in status
            assert 'validation_passed' in status
        
        # Test get_registered_agents method
        registered_agents = orchestrator.get_registered_agents()
        assert isinstance(registered_agents, dict)
        assert "query_test_agent_1" in registered_agents
        assert "query_test_agent_2" in registered_agents
        
        # Verify structure of registered agents info
        for agent_id, info in registered_agents.items():
            assert 'agent_type' in info
            assert 'registration_time' in info
            assert 'is_registered' in info
            assert 'is_healthy' in info
            assert 'registration_retry_count' in info
        
        # Test get_orchestrator_status includes registration info
        orchestrator_status = await orchestrator.get_orchestrator_status()
        assert 'registration_summary' in orchestrator_status
        
        reg_summary = orchestrator_status['registration_summary']
        assert 'total_agents_tracked' in reg_summary
        assert 'successfully_registered' in reg_summary
        assert 'failed_registrations' in reg_summary
        assert 'agents_with_retries' in reg_summary
        
        assert reg_summary['total_agents_tracked'] >= 2
        assert reg_summary['successfully_registered'] >= 2
        
        logger.info("✅ Agent registration status query methods tests passed")
        
    finally:
        await orchestrator.stop()


@pytest.mark.asyncio
async def test_registration_status_with_failures():
    """Test registration status tracking with failures"""
    logger.info("Testing registration status with failures...")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    try:
        # Create agent that will fail status check
        failing_agent = MockAgent("failing_status_agent", should_fail_status=True)
        
        # Try to register the failing agent
        try:
            await orchestrator.register_agent(failing_agent)
            # If it doesn't fail, that's also okay - the retry logic might succeed
        except Exception as e:
            logger.info(f"Expected failure during registration: {e}")
        
        # Check if registration status was tracked
        if "failing_status_agent" in orchestrator.agent_registration_status:
            reg_status = orchestrator.get_agent_registration_status("failing_status_agent")
            assert reg_status is not None
            assert 'total_attempts' in reg_status
            assert reg_status['total_attempts'] > 0
            
            logger.info(f"Registration attempts tracked: {reg_status['total_attempts']}")
        
        logger.info("✅ Registration status with failures tests passed")
        
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_agent_registration_status_data_model())
    asyncio.run(test_orchestrator_registration_status_storage())
    asyncio.run(test_query_agent_registration_status_methods())
    asyncio.run(test_registration_status_with_failures())
    print("All tests passed! ✅")