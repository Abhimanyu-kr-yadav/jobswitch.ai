#!/usr/bin/env python3
"""
End-to-end test for agent fallback behavior
"""
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.orchestrator import AgentOrchestrator, AgentTask, TaskPriority
from app.api.jobs import discover_jobs, generate_job_recommendations, calculate_job_compatibility
from app.agents.base import AgentError


async def test_end_to_end_fallback_scenario():
    """Test complete end-to-end fallback scenario"""
    print("Testing end-to-end fallback scenario...")
    print("=" * 60)
    
    # Create orchestrator instance
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Simulate scenario where job_discovery_agent is not registered
    # but other agents are available
    mock_other_agent = Mock()
    mock_other_agent.agent_id = "resume_optimization_agent"
    mock_other_agent.status = "initialized"
    mock_other_agent.get_status = AsyncMock(return_value={"status": "healthy"})
    
    await orchestrator.register_agent(mock_other_agent)
    
    # Verify orchestrator state
    availability_status = orchestrator.get_agent_availability_status()
    print(f"Orchestrator ready: {availability_status['orchestrator_ready']}")
    print(f"Registered agents: {availability_status['registered_agents']}")
    print(f"Total registered: {availability_status['total_registered']}")
    
    # Test 1: Try to create a task for missing job_discovery_agent
    print("\n1. Testing task creation for missing agent...")
    try:
        task_id = await orchestrator.create_task(
            agent_id="job_discovery_agent",
            task_type="discover_jobs",
            payload={"user_id": "test_user", "search_params": {}}
        )
        print("❌ Expected AgentError but task was created")
        assert False, "Expected AgentError"
    except AgentError as e:
        print(f"✓ Caught expected AgentError: {e.message}")
        print(f"  - Requested agent: {e.details['requested_agent']}")
        print(f"  - Available agents: {e.details['registered_agents']}")
        print(f"  - Total registered: {e.details['total_registered']}")
        print(f"  - Orchestrator ready: {e.details['orchestrator_ready']}")
        
        # Verify error details
        assert e.details["requested_agent"] == "job_discovery_agent"
        assert "resume_optimization_agent" in e.details["registered_agents"]
        assert e.details["total_registered"] == 1
        assert e.details["orchestrator_ready"] is True
    
    # Test 2: Verify fallback behavior would be triggered in API layer
    print("\n2. Testing API layer fallback behavior...")
    
    # Mock user and database for API testing
    mock_user = Mock()
    mock_user.user_id = "test_user_123"
    
    mock_db = Mock()
    mock_jobs = [
        Mock(
            job_id="fallback_job_1",
            title="Fallback Software Engineer",
            company="Fallback Tech",
            location="Remote",
            is_active=True,
            scraped_at="2024-01-01T00:00:00",
            to_dict=Mock(return_value={
                "job_id": "fallback_job_1",
                "title": "Fallback Software Engineer",
                "company": "Fallback Tech",
                "location": "Remote"
            })
        )
    ]
    
    # Setup mock query chain
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = mock_jobs
    mock_db.query.return_value = mock_query
    
    # Test the fallback functions directly
    from app.api.jobs import (
        _handle_missing_job_discovery_agent,
        _handle_missing_job_recommendation_agent,
        _handle_missing_job_compatibility_agent
    )
    
    # Test job discovery fallback
    discovery_result = await _handle_missing_job_discovery_agent(mock_user, mock_db, {})
    print(f"✓ Job discovery fallback result: {discovery_result['status']}")
    print(f"  - Success: {discovery_result['success']}")
    print(f"  - Fallback used: {discovery_result['fallback_used']}")
    print(f"  - Jobs found: {len(discovery_result['jobs'])}")
    print(f"  - User message: {discovery_result['user_message'][:100]}...")
    
    # Test job recommendations fallback
    recommendations_result = await _handle_missing_job_recommendation_agent(mock_user, mock_db, 5)
    print(f"✓ Job recommendations fallback result: {recommendations_result['status']}")
    print(f"  - Success: {recommendations_result['success']}")
    print(f"  - Fallback used: {recommendations_result['fallback_used']}")
    
    # Test job compatibility fallback
    compatibility_result = await _handle_missing_job_compatibility_agent(mock_user, mock_db, "test_job")
    print(f"✓ Job compatibility fallback result: {compatibility_result['status']}")
    print(f"  - Success: {compatibility_result['success']}")
    print(f"  - Fallback used: {compatibility_result['fallback_used']}")
    
    # Test 3: Verify graceful degradation
    print("\n3. Testing graceful degradation...")
    
    # All fallback responses should be successful but degraded
    assert discovery_result["success"] is True
    assert discovery_result["fallback_used"] is True
    assert "user_message" in discovery_result
    
    assert recommendations_result["success"] is True
    assert recommendations_result["fallback_used"] is True
    assert "user_message" in recommendations_result
    
    assert compatibility_result["success"] is True
    assert compatibility_result["fallback_used"] is True
    assert "user_message" in compatibility_result
    
    print("✓ All fallback responses provide graceful degradation")
    
    # Test 4: Verify user-friendly error messages
    print("\n4. Testing user-friendly error messages...")
    
    user_messages = [
        discovery_result["user_message"],
        recommendations_result["user_message"],
        compatibility_result["user_message"]
    ]
    
    for i, message in enumerate(user_messages, 1):
        print(f"  Message {i}: {message[:80]}...")
        
        # Verify message characteristics
        assert len(message) > 50, "Message should be descriptive"
        assert "temporarily unavailable" in message, "Should mention temporary unavailability"
        assert "try again" in message, "Should suggest trying again"
        
        # Should not contain technical terms
        technical_terms = ["agent", "orchestrator", "api", "server", "exception", "error"]
        for term in technical_terms:
            assert term not in message.lower(), f"Message should not contain technical term: {term}"
    
    print("✓ All user messages are user-friendly and actionable")
    
    # Test 5: Verify system continues to function
    print("\n5. Testing system continues to function...")
    
    # The orchestrator should still be operational for other agents
    assert orchestrator.is_ready is True
    assert len(orchestrator.agents) == 1
    assert "resume_optimization_agent" in orchestrator.agents
    
    # Should be able to create tasks for available agents
    try:
        task_id = await orchestrator.create_task(
            agent_id="resume_optimization_agent",
            task_type="optimize_resume",
            payload={"user_id": "test_user", "resume_data": {}}
        )
        print(f"✓ Successfully created task for available agent: {task_id}")
    except Exception as e:
        print(f"❌ Failed to create task for available agent: {str(e)}")
        assert False, "Should be able to create tasks for available agents"
    
    # Clean up
    await orchestrator.stop()
    
    print("\n" + "=" * 60)
    print("✅ End-to-end fallback scenario test completed successfully!")
    print("\nSummary:")
    print("- ✓ Missing agent errors provide detailed information")
    print("- ✓ API layer provides graceful fallback responses")
    print("- ✓ User messages are friendly and actionable")
    print("- ✓ System continues to function for available agents")
    print("- ✓ No technical details exposed to users")


async def run_test():
    """Run the end-to-end fallback test"""
    try:
        await test_end_to_end_fallback_scenario()
        return True
    except Exception as e:
        print(f"\n❌ End-to-end test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)