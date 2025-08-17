#!/usr/bin/env python3
"""
Verification test for Task 2: Enhanced agent registration with validation and retry logic
"""
import asyncio
import logging
from datetime import datetime

# Set up logging to see detailed output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from app.core.orchestrator import AgentOrchestrator, AgentRegistrationStatus
from app.agents.base import BaseAgent, AgentError
from app.core.exceptions import AgentException


class MockValidAgent(BaseAgent):
    """Mock agent that passes all validation"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.status = "initialized"
    
    async def _process_request_impl(self, user_input, context):
        return {"result": "mock_response"}
    
    async def _get_recommendations_impl(self, user_profile):
        return [{"recommendation": "mock_recommendation"}]
    
    async def get_status(self):
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": datetime.utcnow().isoformat()
        }


class MockFailingAgent(BaseAgent):
    """Mock agent that fails validation"""
    
    def __init__(self, agent_id: str, fail_on_attempt: int = 1):
        super().__init__(agent_id)
        self.status = "initialized"
        self.attempt_count = 0
        self.fail_on_attempt = fail_on_attempt
    
    async def _process_request_impl(self, user_input, context):
        return {"result": "mock_response"}
    
    async def _get_recommendations_impl(self, user_profile):
        return [{"recommendation": "mock_recommendation"}]
    
    async def get_status(self):
        self.attempt_count += 1
        if self.attempt_count <= self.fail_on_attempt:
            raise Exception(f"Mock failure on attempt {self.attempt_count}")
        
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": datetime.utcnow().isoformat()
        }


async def test_task_2_requirements():
    """
    Test all requirements for Task 2:
    - Add validation to register_agent() method to confirm successful registration
    - Implement retry logic with exponential backoff for failed registrations
    - Add detailed logging for registration attempts and failures
    """
    logger.info("🧪 Starting Task 2 Verification Tests...")
    
    # Test 1: Validation to confirm successful registration
    logger.info("\n📋 Test 1: Registration validation")
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    try:
        # Test successful registration with validation
        agent = MockValidAgent("validation_test_agent")
        await orchestrator.register_agent(agent)
        
        # Verify agent is registered and validated
        assert "validation_test_agent" in orchestrator.agents
        assert "validation_test_agent" in orchestrator.agent_health
        assert "validation_test_agent" in orchestrator.agent_registration_status
        
        reg_status = orchestrator.get_agent_registration_status("validation_test_agent")
        assert reg_status["is_registered"] is True
        assert reg_status["validation_passed"] is True
        assert reg_status["error_message"] is None
        
        logger.info("✅ Registration validation test passed")
        
        # Test 2: Retry logic with exponential backoff
        logger.info("\n🔄 Test 2: Retry logic with exponential backoff")
        
        # Create agent that fails on first attempt but succeeds on second
        failing_agent = MockFailingAgent("retry_test_agent", fail_on_attempt=1)
        
        start_time = datetime.utcnow()
        await orchestrator.register_agent(failing_agent)
        end_time = datetime.utcnow()
        
        # Verify agent eventually registered successfully
        assert "retry_test_agent" in orchestrator.agents
        reg_status = orchestrator.get_agent_registration_status("retry_test_agent")
        assert reg_status["is_registered"] is True
        # The retry count tracks internal retries, total_attempts tracks registration calls
        assert len(reg_status["registration_attempts"]) >= 1  # Should have at least one attempt
        
        # Verify exponential backoff caused delay
        duration = (end_time - start_time).total_seconds()
        assert duration >= 2.0  # Should have waited at least 2 seconds for retry
        
        logger.info("✅ Retry logic with exponential backoff test passed")
        
        # Test 3: Detailed logging for registration attempts and failures
        logger.info("\n📝 Test 3: Detailed logging verification")
        
        # Create agent that fails all attempts
        always_failing_agent = MockFailingAgent("logging_test_agent", fail_on_attempt=999)
        
        try:
            await orchestrator.register_agent(always_failing_agent)
            assert False, "Should have failed"
        except AgentError as e:
            # Verify error was logged and tracked
            reg_status = orchestrator.get_agent_registration_status("logging_test_agent")
            assert reg_status is not None
            assert reg_status["is_registered"] is False
            assert reg_status["error_message"] is not None
            assert reg_status["retry_count"] > 0
            assert len(reg_status["registration_attempts"]) >= 1  # At least one attempt logged
            
            # Verify each attempt was logged
            for attempt in reg_status["registration_attempts"]:
                assert "timestamp" in attempt
                assert "success" in attempt
                assert attempt["success"] is False
                assert "error_message" in attempt
            
            logger.info("✅ Detailed logging verification test passed")
        
        # Test 4: Verify orchestrator readiness checking
        logger.info("\n⏳ Test 4: Orchestrator readiness checking")
        
        # Stop orchestrator to make it not ready
        await orchestrator.stop()
        
        # Try to register agent when not ready
        not_ready_agent = MockValidAgent("not_ready_test_agent")
        try:
            await orchestrator.register_agent(not_ready_agent)
            assert False, "Should have failed when orchestrator not ready"
        except AgentError as e:
            assert "not ready" in str(e).lower()
            logger.info("✅ Orchestrator readiness checking test passed")
        
        logger.info("\n🎉 All Task 2 requirements verified successfully!")
        
        # Print summary of what was implemented
        logger.info("\n📊 Task 2 Implementation Summary:")
        logger.info("✅ Validation to confirm successful registration:")
        logger.info("   - Agent validation before registration")
        logger.info("   - Post-registration verification")
        logger.info("   - Status tracking and reporting")
        
        logger.info("✅ Retry logic with exponential backoff:")
        logger.info("   - Configurable retry attempts (default: 3)")
        logger.info("   - Exponential backoff with jitter")
        logger.info("   - Proper error handling and cleanup")
        
        logger.info("✅ Detailed logging for registration attempts and failures:")
        logger.info("   - Comprehensive logging at all levels")
        logger.info("   - Registration attempt tracking")
        logger.info("   - Error message preservation")
        logger.info("   - Timing and status information")
        
    finally:
        if orchestrator.is_running:
            await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(test_task_2_requirements())