#!/usr/bin/env python3
"""
Test orchestrator fallback behavior and enhanced error handling
"""
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.orchestrator import AgentOrchestrator, AgentTask, TaskPriority, AgentError
from app.agents.base import BaseAgent


async def test_orchestrator_missing_agent_error():
    """Test orchestrator error handling for missing agents"""
    print("Testing orchestrator missing agent error handling...")
    
    # Create orchestrator instance
    orchestrator = AgentOrchestrator()
    
    # Start orchestrator
    await orchestrator.start()
    
    # Register some agents
    mock_agent_1 = Mock(spec=BaseAgent)
    mock_agent_1.agent_id = "test_agent_1"
    mock_agent_1.status = "initialized"
    mock_agent_1.get_status = AsyncMock(return_value={"status": "healthy"})
    
    mock_agent_2 = Mock(spec=BaseAgent)
    mock_agent_2.agent_id = "test_agent_2"
    mock_agent_2.status = "initialized"
    mock_agent_2.get_status = AsyncMock(return_value={"status": "healthy"})
    
    await orchestrator.register_agent(mock_agent_1)
    await orchestrator.register_agent(mock_agent_2)
    
    # Create a task for a missing agent
    task = AgentTask(
        task_id="test_task_123",
        agent_id="missing_agent",
        task_type="test_task",
        payload={"test": "data"},
        priority=TaskPriority.MEDIUM
    )
    
    # Try to submit the task and verify enhanced error
    try:
        await orchestrator.submit_task(task)
        assert False, "Expected AgentError to be raised"
    except AgentError as e:
        # Verify enhanced error information
        assert e.agent_id == "missing_agent"
        assert "not registered" in e.message
        assert "Available agents" in e.message
        assert "test_agent_1" in e.message
        assert "test_agent_2" in e.message
        
        # Verify error details
        assert hasattr(e, 'details')
        assert e.details["requested_agent"] == "missing_agent"
        assert e.details["total_registered"] == 2
        assert e.details["orchestrator_ready"] is True
        assert "test_agent_1" in e.details["registered_agents"]
        assert "test_agent_2" in e.details["registered_agents"]
    
    # Stop orchestrator
    await orchestrator.stop()
    
    print("✓ Orchestrator missing agent error test passed")


async def test_orchestrator_agent_availability_status():
    """Test orchestrator agent availability status reporting"""
    print("Testing orchestrator agent availability status...")
    
    # Create orchestrator instance
    orchestrator = AgentOrchestrator()
    
    # Start orchestrator
    await orchestrator.start()
    
    # Register some agents
    mock_agent_1 = Mock(spec=BaseAgent)
    mock_agent_1.agent_id = "healthy_agent"
    mock_agent_1.status = "initialized"
    mock_agent_1.get_status = AsyncMock(return_value={"status": "healthy"})
    
    await orchestrator.register_agent(mock_agent_1)
    
    # Get availability status
    status = orchestrator.get_agent_availability_status()
    
    # Verify status information
    assert status["total_registered"] == 1
    assert "healthy_agent" in status["registered_agents"]
    assert "healthy_agent" in status["healthy_agents"]
    assert len(status["unhealthy_agents"]) == 0
    assert len(status["failed_registrations"]) == 0
    assert status["orchestrator_ready"] is True
    assert status["initialization_phase"] == "ready"
    assert status["initialization_time"] is not None
    
    # Stop orchestrator
    await orchestrator.stop()
    
    print("✓ Orchestrator agent availability status test passed")


async def test_orchestrator_registered_agents_info():
    """Test orchestrator registered agents information"""
    print("Testing orchestrator registered agents info...")
    
    # Create orchestrator instance
    orchestrator = AgentOrchestrator()
    
    # Start orchestrator
    await orchestrator.start()
    
    # Register an agent
    mock_agent = Mock(spec=BaseAgent)
    mock_agent.agent_id = "info_test_agent"
    mock_agent.status = "initialized"
    mock_agent.get_status = AsyncMock(return_value={"status": "healthy"})
    
    await orchestrator.register_agent(mock_agent)
    
    # Get registered agents info
    agents_info = orchestrator.get_registered_agents()
    
    # Verify agent information
    assert "info_test_agent" in agents_info
    agent_info = agents_info["info_test_agent"]
    
    assert agent_info["is_registered"] is True
    assert agent_info["health_status"] is not None
    assert agent_info["registration_status"] is not None
    
    # Verify health status details
    health_status = agent_info["health_status"]
    assert health_status["agent_id"] == "info_test_agent"
    assert health_status["is_healthy"] is True
    
    # Verify registration status details
    registration_status = agent_info["registration_status"]
    assert registration_status["agent_id"] == "info_test_agent"
    assert registration_status["is_registered"] is True
    assert registration_status["validation_passed"] is True
    
    # Stop orchestrator
    await orchestrator.stop()
    
    print("✓ Orchestrator registered agents info test passed")


async def run_tests():
    """Run all orchestrator fallback tests"""
    print("Testing orchestrator fallback behavior...")
    print("=" * 50)
    
    try:
        await test_orchestrator_missing_agent_error()
        await test_orchestrator_agent_availability_status()
        await test_orchestrator_registered_agents_info()
        
        print("=" * 50)
        print("✅ All orchestrator fallback tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)