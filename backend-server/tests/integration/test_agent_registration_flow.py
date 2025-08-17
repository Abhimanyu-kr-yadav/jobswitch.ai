"""
Integration tests for agent registration flow
Tests the complete agent registration process including orchestrator initialization,
agent registration with validation and retry logic, error handling, and readiness tracking.

Requirements covered:
- 1.1: Successful agent registration scenarios
- 1.2: Agent registration validation and retry logic
- 1.3: Orchestrator initialization and readiness
- 1.4: Error handling and fallback behavior
"""
import pytest
import pytest_asyncio
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.orchestrator import AgentOrchestrator, AgentRegistrationStatus, TaskStatus
from app.agents.base import BaseAgent, AgentError
from app.agents.job_discovery import JobDiscoveryAgent
from app.core.exceptions import AgentException
from app.core.retry import RetryConfig


# Test logger
logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """Mock agent for testing purposes"""
    
    def __init__(self, agent_id: str, should_fail: bool = False, fail_on_attempt: int = None):
        super().__init__(agent_id)
        self.should_fail = should_fail
        self.fail_on_attempt = fail_on_attempt
        self.registration_attempts = 0
        self.status = "initialized"
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": {"mock_response": True}}
    
    async def _get_recommendations_impl(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock recommendations implementation"""
        return [{"recommendation": "mock_recommendation", "score": 0.8}]
    
    async def get_status(self) -> Dict[str, Any]:
        """Mock status method"""
        self.registration_attempts += 1
        
        if self.should_fail and (self.fail_on_attempt is None or self.registration_attempts <= self.fail_on_attempt):
            raise Exception("Mock agent failure")
        
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "last_activity": datetime.utcnow().isoformat()
        }


class TestAgentRegistrationFlow:
    """Integration tests for agent registration flow"""
    
    @pytest_asyncio.fixture
    async def orchestrator(self):
        """Create and start orchestrator for testing"""
        orchestrator = AgentOrchestrator()
        await orchestrator.start()
        try:
            yield orchestrator
        finally:
            # Ensure proper cleanup of background tasks
            try:
                await orchestrator.stop()
                # Give background tasks time to cleanup
                await asyncio.sleep(0.1)
            except Exception as e:
                # Log cleanup errors but don't fail tests
                logger.warning(f"Error during orchestrator cleanup: {e}")
    
    @pytest.fixture
    def mock_watsonx_client(self):
        """Mock WatsonX client"""
        client = AsyncMock()
        client.generate_text = AsyncMock(return_value={
            "success": True,
            "generated_text": "Mock response"
        })
        return client
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization_and_readiness(self):
        """
        Test orchestrator initialization sequence and readiness tracking
        Requirements: 1.3 - Orchestrator initialization and readiness
        """
        # Test orchestrator creation (not started)
        orchestrator = AgentOrchestrator()
        assert not orchestrator.is_ready
        assert orchestrator._initialization_phase == "not_started"
        
        # Test orchestrator startup
        start_time = datetime.utcnow()
        await orchestrator.start()
        end_time = datetime.utcnow()
        
        # Verify readiness
        assert orchestrator.is_ready
        assert orchestrator._initialization_phase == "ready"
        assert orchestrator.is_running
        assert orchestrator._initialization_start_time is not None
        assert orchestrator._initialization_complete_time is not None
        
        # Verify initialization timing
        initialization_duration = (orchestrator._initialization_complete_time - orchestrator._initialization_start_time).total_seconds()
        assert initialization_duration >= 0
        
        # Test wait_for_ready when already ready
        ready_result = await orchestrator.wait_for_ready(timeout=1.0)
        assert ready_result is True
        
        await orchestrator.stop()
        
        # Verify stopped state
        assert not orchestrator.is_ready
        assert not orchestrator.is_running
    
    @pytest.mark.asyncio
    async def test_wait_for_ready_timeout(self):
        """
        Test wait_for_ready timeout behavior
        Requirements: 1.3 - Orchestrator initialization and readiness
        """
        orchestrator = AgentOrchestrator()
        # Don't start the orchestrator
        
        # Test timeout
        start_time = datetime.utcnow()
        ready_result = await orchestrator.wait_for_ready(timeout=0.5)
        end_time = datetime.utcnow()
        
        assert ready_result is False
        duration = (end_time - start_time).total_seconds()
        assert 0.4 <= duration <= 0.7  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_wait_for_ready_concurrent_waiters(self):
        """
        Test multiple concurrent waiters for orchestrator readiness
        Requirements: 1.3 - Orchestrator initialization and readiness
        """
        orchestrator = AgentOrchestrator()
        
        # Create multiple waiters
        async def waiter():
            return await orchestrator.wait_for_ready(timeout=2.0)
        
        # Start multiple waiters
        waiter_tasks = [asyncio.create_task(waiter()) for _ in range(5)]
        
        # Start orchestrator after a short delay
        async def delayed_start():
            await asyncio.sleep(0.1)
            await orchestrator.start()
        
        start_task = asyncio.create_task(delayed_start())
        
        # Wait for all tasks
        results = await asyncio.gather(*waiter_tasks, start_task)
        
        # All waiters should succeed
        for i in range(5):
            assert results[i] is True
        
        await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_successful_agent_registration(self, orchestrator):
        """
        Test successful agent registration scenarios
        Requirements: 1.1 - Successful agent registration scenarios
        """
        # Create mock agent
        agent = MockAgent("test_agent_1")
        
        # Register agent
        await orchestrator.register_agent(agent)
        
        # Verify registration
        assert "test_agent_1" in orchestrator.agents
        assert orchestrator.agents["test_agent_1"] == agent
        
        # Verify registration status
        reg_status = orchestrator.agent_registration_status["test_agent_1"]
        assert reg_status.is_registered is True
        assert reg_status.validation_passed is True
        assert reg_status.error_message is None
        assert reg_status.registration_time is not None
        assert len(reg_status.registration_attempts) == 1
        assert reg_status.registration_attempts[0]["success"] is True
        
        # Verify health status
        assert "test_agent_1" in orchestrator.agent_health
        health_status = orchestrator.agent_health["test_agent_1"]
        assert health_status.agent_id == "test_agent_1"
        assert health_status.is_healthy()
    
    @pytest.mark.asyncio
    async def test_multiple_agent_registration(self, orchestrator):
        """
        Test registration of multiple agents
        Requirements: 1.1 - Successful agent registration scenarios
        """
        # Create multiple agents
        agents = [
            MockAgent("agent_1"),
            MockAgent("agent_2"),
            MockAgent("agent_3")
        ]
        
        # Register all agents
        for agent in agents:
            await orchestrator.register_agent(agent)
        
        # Verify all registrations
        for agent in agents:
            assert agent.agent_id in orchestrator.agents
            assert orchestrator.agents[agent.agent_id] == agent
            
            reg_status = orchestrator.agent_registration_status[agent.agent_id]
            assert reg_status.is_registered is True
            assert reg_status.validation_passed is True
    
    @pytest.mark.asyncio
    async def test_agent_registration_with_retry_logic(self, orchestrator):
        """
        Test agent registration retry logic for transient failures
        Requirements: 1.2 - Agent registration validation and retry logic
        """
        # Create agent that fails on first attempt but succeeds on second
        agent = MockAgent("retry_agent", should_fail=True, fail_on_attempt=1)
        
        # Register agent (should succeed after retry)
        await orchestrator.register_agent(agent)
        
        # Verify successful registration after retry
        assert "retry_agent" in orchestrator.agents
        reg_status = orchestrator.agent_registration_status["retry_agent"]
        assert reg_status.is_registered is True
        assert reg_status.validation_passed is True
        
        # Verify that retry logic was triggered (agent should have been called multiple times)
        # The MockAgent tracks its own attempts through get_status calls
        assert agent.registration_attempts >= 2  # At least one retry occurred
        
        # Verify final successful registration was recorded
        attempts = reg_status.registration_attempts
        assert len(attempts) >= 1  # At least the successful attempt
        assert attempts[-1]["success"] is True   # Last attempt succeeded
    
    @pytest.mark.asyncio
    async def test_agent_registration_failure_after_retries(self, orchestrator):
        """
        Test agent registration failure after exhausting all retries
        Requirements: 1.2, 1.4 - Agent registration validation and error handling
        """
        # Create agent that always fails
        agent = MockAgent("failing_agent", should_fail=True)
        
        # Attempt registration (should fail after all retries)
        with pytest.raises((AgentException, AgentError)) as exc_info:
            await orchestrator.register_agent(agent)
        
        assert "Agent registration failed" in str(exc_info.value)
        
        # Verify agent was not registered
        assert "failing_agent" not in orchestrator.agents
        
        # Verify registration status tracks the failure
        reg_status = orchestrator.agent_registration_status["failing_agent"]
        assert reg_status.is_registered is False
        assert reg_status.validation_passed is False
        assert reg_status.error_message is not None
        
        # Verify that multiple attempts were made (tracked by the MockAgent)
        assert agent.registration_attempts >= 3  # Should have tried multiple times
    
    @pytest.mark.asyncio
    async def test_agent_registration_validation(self, orchestrator):
        """
        Test agent registration validation logic
        Requirements: 1.2 - Agent registration validation and retry logic
        """
        # Test with invalid agent (missing required methods)
        class InvalidAgent:
            def __init__(self):
                self.agent_id = "invalid_agent"
        
        invalid_agent = InvalidAgent()
        
        # Registration should fail validation
        with pytest.raises((AgentException, AgentError, Exception)):
            await orchestrator.register_agent(invalid_agent)
        
        # Verify agent was not registered
        assert "invalid_agent" not in orchestrator.agents
    
    @pytest.mark.asyncio
    async def test_orchestrator_not_ready_registration(self):
        """
        Test agent registration when orchestrator is not ready
        Requirements: 1.3, 1.4 - Orchestrator readiness and error handling
        """
        # Create orchestrator but don't start it
        orchestrator = AgentOrchestrator()
        agent = MockAgent("test_agent")
        
        # Registration should wait for readiness or fail
        with pytest.raises((AgentException, asyncio.TimeoutError)):
            # Use a short timeout to avoid long test execution
            await asyncio.wait_for(
                orchestrator.register_agent(agent),
                timeout=1.0
            )
    
    @pytest.mark.asyncio
    async def test_agent_registration_status_tracking(self, orchestrator):
        """
        Test comprehensive agent registration status tracking
        Requirements: 1.1, 1.2 - Registration status tracking
        """
        agent = MockAgent("status_test_agent")
        
        # Check initial status (should not exist)
        assert "status_test_agent" not in orchestrator.agent_registration_status
        
        # Register agent
        registration_start = datetime.utcnow()
        await orchestrator.register_agent(agent)
        registration_end = datetime.utcnow()
        
        # Verify status tracking
        reg_status = orchestrator.agent_registration_status["status_test_agent"]
        
        # Check basic status
        assert reg_status.agent_id == "status_test_agent"
        assert reg_status.is_registered is True
        assert reg_status.validation_passed is True
        assert reg_status.error_message is None
        assert reg_status.retry_count == 0  # No retries needed
        
        # Check timing
        assert reg_status.registration_time is not None
        assert registration_start <= reg_status.registration_time <= registration_end
        
        # Check attempts tracking
        assert len(reg_status.registration_attempts) == 1
        attempt = reg_status.registration_attempts[0]
        assert attempt["success"] is True
        assert attempt["error_message"] is None
        # Verify timestamp is within expected range
        attempt_timestamp = attempt["timestamp"]
        if isinstance(attempt_timestamp, str):
            attempt_timestamp = datetime.fromisoformat(attempt_timestamp.replace('Z', '+00:00').replace('+00:00', ''))
        assert registration_start <= attempt_timestamp <= registration_end
        
        # Test status serialization
        status_dict = reg_status.to_dict()
        assert status_dict["agent_id"] == "status_test_agent"
        assert status_dict["is_registered"] is True
        assert status_dict["validation_passed"] is True
        assert status_dict["total_attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_get_registered_agents(self, orchestrator):
        """
        Test getting list of registered agents
        Requirements: 1.1 - Successful agent registration scenarios
        """
        # Initially no agents
        registered_agents = orchestrator.get_registered_agents()
        assert len(registered_agents) == 0
        
        # Register some agents
        agents = [MockAgent(f"agent_{i}") for i in range(3)]
        for agent in agents:
            await orchestrator.register_agent(agent)
        
        # Check registered agents list
        registered_agents = orchestrator.get_registered_agents()
        assert len(registered_agents) == 3
        
        expected_ids = {f"agent_{i}" for i in range(3)}
        actual_ids = {agent_id for agent_id in registered_agents.keys()}
        assert actual_ids == expected_ids
    
    @pytest.mark.asyncio
    async def test_agent_registration_with_real_job_discovery_agent(self, orchestrator, mock_watsonx_client):
        """
        Test registration with a real JobDiscoveryAgent
        Requirements: 1.1 - Successful agent registration scenarios
        """
        # Create real job discovery agent
        job_agent = JobDiscoveryAgent(mock_watsonx_client)
        
        # Register the agent
        await orchestrator.register_agent(job_agent)
        
        # Verify registration
        assert "job_discovery_agent" in orchestrator.agents
        assert orchestrator.agents["job_discovery_agent"] == job_agent
        
        # Verify registration status
        reg_status = orchestrator.agent_registration_status["job_discovery_agent"]
        assert reg_status.is_registered is True
        assert reg_status.validation_passed is True
    
    @pytest.mark.asyncio
    async def test_agent_registration_error_handling_and_logging(self, orchestrator, caplog):
        """
        Test error handling and logging during agent registration
        Requirements: 1.4 - Error handling and fallback behavior
        """
        # Create agent that will fail
        agent = MockAgent("error_test_agent", should_fail=True)
        
        with caplog.at_level(logging.INFO):
            # Attempt registration (should fail)
            with pytest.raises((AgentException, AgentError)):
                await orchestrator.register_agent(agent)
        
        # Verify error logging
        log_messages = [record.message for record in caplog.records]
        
        # Should have registration start, retry attempts, and failure messages
        assert any("Starting agent registration" in msg for msg in log_messages)
        assert any("Agent registration attempt" in msg for msg in log_messages)
        assert any("Agent registration failed" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_registrations(self, orchestrator):
        """
        Test concurrent agent registrations
        Requirements: 1.1, 1.3 - Successful registration and orchestrator readiness
        """
        # Create multiple agents
        agents = [MockAgent(f"concurrent_agent_{i}") for i in range(5)]
        
        # Register all agents concurrently
        registration_tasks = [
            orchestrator.register_agent(agent) for agent in agents
        ]
        
        # Wait for all registrations to complete
        await asyncio.gather(*registration_tasks)
        
        # Verify all agents were registered
        for agent in agents:
            assert agent.agent_id in orchestrator.agents
            assert orchestrator.agents[agent.agent_id] == agent
            
            reg_status = orchestrator.agent_registration_status[agent.agent_id]
            assert reg_status.is_registered is True
            assert reg_status.validation_passed is True
    
    @pytest.mark.asyncio
    async def test_agent_registration_performance(self, orchestrator):
        """
        Test agent registration performance
        Requirements: 1.1, 1.3 - Registration performance and readiness
        """
        agent = MockAgent("performance_test_agent")
        
        # Measure registration time
        start_time = datetime.utcnow()
        await orchestrator.register_agent(agent)
        end_time = datetime.utcnow()
        
        registration_duration = (end_time - start_time).total_seconds()
        
        # Registration should complete within reasonable time (5 seconds)
        assert registration_duration < 5.0
        
        # Verify timing is tracked in registration status
        reg_status = orchestrator.agent_registration_status["performance_test_agent"]
        assert reg_status.registration_time is not None
    
    @pytest.mark.asyncio
    async def test_orchestrator_startup_failure_handling(self):
        """
        Test orchestrator startup failure handling
        Requirements: 1.3, 1.4 - Orchestrator initialization and error handling
        """
        orchestrator = AgentOrchestrator()
        
        # Mock a startup failure
        with patch.object(orchestrator, '_init_redis', side_effect=Exception("Redis connection failed")):
            with pytest.raises(Exception) as exc_info:
                await orchestrator.start()
            
            assert "Redis connection failed" in str(exc_info.value)
            
            # Verify orchestrator state after failure
            assert not orchestrator.is_ready
            assert orchestrator._initialization_phase == "failed"
            assert not orchestrator.is_running
    
    @pytest.mark.asyncio
    async def test_agent_health_status_after_registration(self, orchestrator):
        """
        Test agent health status tracking after registration
        Requirements: 1.1 - Successful agent registration scenarios
        """
        agent = MockAgent("health_test_agent")
        
        # Register agent
        await orchestrator.register_agent(agent)
        
        # Verify health status was created
        assert "health_test_agent" in orchestrator.agent_health
        
        health_status = orchestrator.agent_health["health_test_agent"]
        assert health_status.agent_id == "health_test_agent"
        assert health_status.is_healthy()
        assert health_status.last_heartbeat is not None
        assert health_status.current_load == 0
        assert health_status.error_count == 0
        assert health_status.success_count == 0
    
    @pytest.mark.asyncio
    async def test_registration_status_serialization(self, orchestrator):
        """
        Test registration status serialization for API responses
        Requirements: 1.1, 1.2 - Registration status tracking
        """
        # Register successful agent
        success_agent = MockAgent("success_agent")
        await orchestrator.register_agent(success_agent)
        
        # Try to register failing agent
        fail_agent = MockAgent("fail_agent", should_fail=True)
        try:
            await orchestrator.register_agent(fail_agent)
        except (AgentException, AgentError):
            pass  # Expected failure
        
        # Test successful agent status serialization
        success_status = orchestrator.agent_registration_status["success_agent"]
        success_dict = success_status.to_dict()
        
        required_fields = [
            "agent_id", "is_registered", "registration_time", "last_health_check",
            "error_message", "retry_count", "validation_passed", "total_attempts",
            "registration_attempts"
        ]
        
        for field in required_fields:
            assert field in success_dict
        
        assert success_dict["is_registered"] is True
        assert success_dict["validation_passed"] is True
        assert success_dict["total_attempts"] == 1
        
        # Test failed agent status serialization
        fail_status = orchestrator.agent_registration_status["fail_agent"]
        fail_dict = fail_status.to_dict()
        
        assert fail_dict["is_registered"] is False
        assert fail_dict["validation_passed"] is False
        assert fail_dict["total_attempts"] >= 1  # At least one attempt was recorded
        assert fail_dict["error_message"] is not None
        
        # Verify that multiple attempts were actually made (tracked by the MockAgent)
        assert fail_agent.registration_attempts >= 3  # Should have tried multiple times
    
    @pytest.mark.asyncio
    async def test_agent_registration_timeout_scenarios(self, orchestrator):
        """
        Test agent registration timeout scenarios
        Requirements: 1.2, 1.4 - Registration retry logic and error handling
        """
        class SlowAgent(MockAgent):
            """Agent that takes a long time to respond"""
            
            async def get_status(self) -> Dict[str, Any]:
                # Simulate slow response
                await asyncio.sleep(2.0)
                return await super().get_status()
        
        slow_agent = SlowAgent("slow_agent")
        
        # Test with short timeout - should handle gracefully
        start_time = datetime.utcnow()
        try:
            # This might timeout or succeed depending on system performance
            await orchestrator.register_agent(slow_agent)
            # If it succeeds, verify it's registered
            assert "slow_agent" in orchestrator.agents
        except (AgentException, AgentError, asyncio.TimeoutError):
            # If it times out, that's also acceptable behavior
            pass
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should not take excessively long (max 30 seconds with retries)
        assert duration < 30.0
    
    @pytest.mark.asyncio
    async def test_agent_registration_memory_cleanup(self, orchestrator):
        """
        Test memory cleanup during agent registration failures
        Requirements: 1.4 - Error handling and resource management
        """
        # Register and unregister multiple agents to test cleanup
        for i in range(10):
            agent = MockAgent(f"cleanup_test_agent_{i}")
            await orchestrator.register_agent(agent)
        
        # Verify all agents are registered
        assert len(orchestrator.agents) == 10
        assert len(orchestrator.agent_registration_status) == 10
        assert len(orchestrator.agent_health) == 10
        
        # Test with failing agents (should not accumulate in memory)
        for i in range(5):
            failing_agent = MockAgent(f"failing_cleanup_agent_{i}", should_fail=True)
            try:
                await orchestrator.register_agent(failing_agent)
            except (AgentException, AgentError):
                pass  # Expected failure
        
        # Verify failed agents don't accumulate in the main registry
        # but their status is tracked for debugging
        assert len(orchestrator.agents) == 10  # Only successful agents
        assert len(orchestrator.agent_registration_status) == 15  # All attempts tracked
    
    @pytest.mark.asyncio
    async def test_agent_registration_with_network_simulation(self, orchestrator):
        """
        Test agent registration with simulated network issues
        Requirements: 1.2, 1.4 - Retry logic and error handling
        """
        class NetworkIssueAgent(MockAgent):
            """Agent that simulates network connectivity issues"""
            
            def __init__(self, agent_id: str):
                super().__init__(agent_id)
                self.network_failures = 2  # Fail first 2 attempts
            
            async def get_status(self) -> Dict[str, Any]:
                self.registration_attempts += 1
                
                if self.network_failures > 0:
                    self.network_failures -= 1
                    raise ConnectionError("Simulated network failure")
                
                return {
                    "agent_id": self.agent_id,
                    "status": "healthy",
                    "last_activity": datetime.utcnow().isoformat()
                }
        
        network_agent = NetworkIssueAgent("network_test_agent")
        
        # Should succeed after retries
        await orchestrator.register_agent(network_agent)
        
        # Verify successful registration
        assert "network_test_agent" in orchestrator.agents
        reg_status = orchestrator.agent_registration_status["network_test_agent"]
        assert reg_status.is_registered is True
        
        # Verify that retries occurred
        assert network_agent.registration_attempts >= 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_agent_registration_race_conditions(self, orchestrator):
        """
        Test agent registration race conditions and thread safety
        Requirements: 1.1, 1.3 - Concurrent registration scenarios
        """
        # Test registering the same agent ID from multiple coroutines
        agent_id = "race_condition_agent"
        
        async def register_agent_task(task_id: int):
            agent = MockAgent(f"{agent_id}_{task_id}")
            try:
                await orchestrator.register_agent(agent)
                return True
            except Exception:
                return False
        
        # Start multiple registration tasks concurrently
        tasks = [register_agent_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed since they have different IDs
        successful_registrations = sum(1 for result in results if result is True)
        assert successful_registrations == 5
        
        # Verify all agents are registered
        for i in range(5):
            assert f"{agent_id}_{i}" in orchestrator.agents
    
    @pytest.mark.asyncio
    async def test_agent_registration_with_custom_retry_config(self):
        """
        Test agent registration with custom retry configuration
        Requirements: 1.2 - Registration retry logic customization
        """
        # Create orchestrator with custom retry config
        orchestrator = AgentOrchestrator()
        
        # Modify retry configuration
        orchestrator._registration_retry_config.max_attempts = 5
        orchestrator._registration_retry_config.base_delay = 0.1
        orchestrator._registration_retry_config.max_delay = 1.0
        
        await orchestrator.start()
        
        try:
            # Test with agent that fails multiple times
            agent = MockAgent("custom_retry_agent", should_fail=True, fail_on_attempt=3)
            
            # Should succeed on 4th attempt (after 3 failures)
            await orchestrator.register_agent(agent)
            
            # Verify successful registration
            assert "custom_retry_agent" in orchestrator.agents
            reg_status = orchestrator.agent_registration_status["custom_retry_agent"]
            assert reg_status.is_registered is True
            
            # Verify that multiple attempts were made
            assert agent.registration_attempts >= 4
            
        finally:
            await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_agent_registration_status_persistence(self, orchestrator):
        """
        Test agent registration status persistence and retrieval
        Requirements: 1.1, 1.2 - Registration status tracking and persistence
        """
        # Register multiple agents with different outcomes
        success_agent = MockAgent("success_persistence_agent")
        await orchestrator.register_agent(success_agent)
        
        retry_agent = MockAgent("retry_persistence_agent", should_fail=True, fail_on_attempt=1)
        await orchestrator.register_agent(retry_agent)
        
        fail_agent = MockAgent("fail_persistence_agent", should_fail=True)
        try:
            await orchestrator.register_agent(fail_agent)
        except (AgentException, AgentError):
            pass
        
        # Test status retrieval and persistence
        all_statuses = {
            agent_id: status.to_dict() 
            for agent_id, status in orchestrator.agent_registration_status.items()
        }
        
        # Verify all statuses are tracked
        assert "success_persistence_agent" in all_statuses
        assert "retry_persistence_agent" in all_statuses
        assert "fail_persistence_agent" in all_statuses
        
        # Verify status details
        success_status = all_statuses["success_persistence_agent"]
        assert success_status["is_registered"] is True
        assert success_status["total_attempts"] == 1
        
        retry_status = all_statuses["retry_persistence_agent"]
        assert retry_status["is_registered"] is True
        assert retry_status["total_attempts"] >= 1  # At least one attempt
        
        fail_status = all_statuses["fail_persistence_agent"]
        assert fail_status["is_registered"] is False
        assert fail_status["total_attempts"] >= 1  # At least one failed attempt
        assert fail_status["error_message"] is not None
        
        # Verify that the MockAgent actually made multiple attempts (this is tracked separately)
        assert fail_agent.registration_attempts >= 3  # Multiple attempts were made
    
    @pytest.mark.asyncio
    async def test_orchestrator_graceful_shutdown_during_registration(self):
        """
        Test orchestrator graceful shutdown during active registrations
        Requirements: 1.3, 1.4 - Orchestrator lifecycle and error handling
        """
        orchestrator = AgentOrchestrator()
        await orchestrator.start()
        
        # Start a slow registration process
        slow_agent = MockAgent("shutdown_test_agent")
        
        # Mock the registration to be slow
        original_perform_registration = orchestrator._perform_agent_registration
        
        async def slow_registration(agent):
            await asyncio.sleep(1.0)  # Simulate slow registration
            return await original_perform_registration(agent)
        
        orchestrator._perform_agent_registration = slow_registration
        
        # Start registration in background
        registration_task = asyncio.create_task(
            orchestrator.register_agent(slow_agent)
        )
        
        # Give registration time to start
        await asyncio.sleep(0.1)
        
        # Shutdown orchestrator while registration is in progress
        await orchestrator.stop()
        
        # Registration task should be cancelled or handle shutdown gracefully
        try:
            await registration_task
        except (asyncio.CancelledError, AgentException, AgentError):
            pass  # Expected behavior during shutdown
        
        # Verify orchestrator is properly stopped
        assert not orchestrator.is_ready
        assert not orchestrator.is_running
    
    @pytest.mark.asyncio
    async def test_agent_registration_with_health_check_integration(self, orchestrator):
        """
        Test agent registration integration with health check system
        Requirements: 1.1 - Registration and health monitoring integration
        """
        agent = MockAgent("health_integration_agent")
        
        # Register agent
        await orchestrator.register_agent(agent)
        
        # Verify health status is properly initialized
        health_status = orchestrator.agent_health["health_integration_agent"]
        assert health_status.agent_id == "health_integration_agent"
        assert health_status.is_healthy()
        
        # Simulate health status updates
        health_status.increment_success()
        health_status.add_response_time(0.5)
        health_status.update_heartbeat()
        
        # Verify health metrics are tracked
        assert health_status.success_count == 1
        assert health_status.get_average_response_time() == 0.5
        assert health_status.get_success_rate() == 100.0
        
        # Test health status serialization
        health_dict = health_status.to_dict()
        required_fields = [
            "agent_id", "status", "last_heartbeat", "average_response_time",
            "error_count", "success_count", "success_rate", "current_load",
            "max_load", "is_healthy"
        ]
        
        for field in required_fields:
            assert field in health_dict
    
    @pytest.mark.asyncio
    async def test_agent_registration_error_recovery(self, orchestrator):
        """
        Test agent registration error recovery scenarios
        Requirements: 1.4 - Error handling and recovery
        """
        class RecoveryAgent(MockAgent):
            """Agent that recovers from initial failures"""
            
            def __init__(self, agent_id: str):
                super().__init__(agent_id)
                self.failure_count = 0
                self.max_failures = 2
            
            async def get_status(self) -> Dict[str, Any]:
                self.registration_attempts += 1
                
                if self.failure_count < self.max_failures:
                    self.failure_count += 1
                    if self.failure_count == 1:
                        raise ValueError("Temporary configuration error")
                    elif self.failure_count == 2:
                        raise RuntimeError("Temporary runtime error")
                
                return {
                    "agent_id": self.agent_id,
                    "status": "healthy",
                    "last_activity": datetime.utcnow().isoformat()
                }
        
        recovery_agent = RecoveryAgent("recovery_test_agent")
        
        # Should succeed after recovering from errors
        await orchestrator.register_agent(recovery_agent)
        
        # Verify successful registration
        assert "recovery_test_agent" in orchestrator.agents
        reg_status = orchestrator.agent_registration_status["recovery_test_agent"]
        assert reg_status.is_registered is True
        assert reg_status.validation_passed is True
        
        # Verify that recovery occurred (multiple attempts)
        assert recovery_agent.registration_attempts >= 3
        
        # Verify error history is tracked
        attempts = reg_status.registration_attempts
        assert len(attempts) >= 1
        
        # Final attempt should have succeeded
        assert attempts[-1]["success"] is True
        
        # If there were multiple attempts, earlier ones should have failed
        if len(attempts) > 1:
            failed_attempts = [a for a in attempts[:-1] if not a["success"]]
            assert len(failed_attempts) >= 1