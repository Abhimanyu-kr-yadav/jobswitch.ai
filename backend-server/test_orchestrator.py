"""
Test Agent Orchestrator Implementation
Tests the enhanced orchestration system with WatsonX integration
"""
import asyncio
import logging
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.core.orchestrator import (
    AgentOrchestrator, AgentTask, AgentMessage, AgentHealthStatus,
    TaskStatus, TaskPriority, AgentStatus, MessageType
)
from app.agents.base import BaseAgent, AgentResponse

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, agent_id: str, delay: float = 0.1):
        super().__init__(agent_id)
        self.delay = delay
        self.processed_requests = []
    
    async def process_request(self, user_input: dict, context: dict) -> dict:
        """Mock request processing with configurable delay"""
        await asyncio.sleep(self.delay)
        self.processed_requests.append(user_input)
        
        return {
            "success": True,
            "agent_id": self.agent_id,
            "processed_data": user_input,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_recommendations(self, user_profile: dict) -> list:
        """Mock recommendations"""
        return [
            {
                "type": "test_recommendation",
                "agent_id": self.agent_id,
                "data": user_profile
            }
        ]


async def test_orchestrator_initialization():
    """Test orchestrator initialization"""
    logger.info("Testing orchestrator initialization...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    assert orchestrator.is_running
    assert len(orchestrator.agents) == 0
    assert len(orchestrator.task_queue) == 0
    
    await orchestrator.stop()
    assert not orchestrator.is_running
    
    logger.info("✓ Orchestrator initialization test passed")


async def test_agent_registration():
    """Test agent registration and health monitoring"""
    logger.info("Testing agent registration...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Create mock agents
    agent1 = MockAgent("test_agent_1")
    agent2 = MockAgent("test_agent_2")
    
    # Register agents
    await orchestrator.register_agent(agent1)
    await orchestrator.register_agent(agent2)
    
    assert len(orchestrator.agents) == 2
    assert "test_agent_1" in orchestrator.agents
    assert "test_agent_2" in orchestrator.agents
    
    # Check health status creation
    assert "test_agent_1" in orchestrator.agent_health
    assert "test_agent_2" in orchestrator.agent_health
    
    # Test agent status retrieval
    status1 = await orchestrator.get_agent_status("test_agent_1")
    assert status1 is not None
    assert status1["agent_id"] == "test_agent_1"
    
    # Unregister agent
    await orchestrator.unregister_agent("test_agent_1")
    assert len(orchestrator.agents) == 1
    assert "test_agent_1" not in orchestrator.agents
    
    await orchestrator.stop()
    logger.info("✓ Agent registration test passed")


async def test_task_creation_and_execution():
    """Test task creation and execution"""
    logger.info("Testing task creation and execution...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Register mock agent
    agent = MockAgent("test_agent")
    await orchestrator.register_agent(agent)
    
    # Create and submit task
    task_id = await orchestrator.create_task(
        agent_id="test_agent",
        task_type="test_task",
        payload={"test_data": "hello world"},
        priority=TaskPriority.HIGH
    )
    
    assert task_id is not None
    assert len(orchestrator.task_queue) == 1
    
    # Wait for task processing
    await asyncio.sleep(0.5)
    
    # Check task completion
    task_status = await orchestrator.get_task_status(task_id)
    assert task_status is not None
    assert task_status["status"] == "completed"
    assert task_status["task_id"] == task_id
    
    # Verify agent processed the request
    assert len(agent.processed_requests) == 1
    assert agent.processed_requests[0]["test_data"] == "hello world"
    
    await orchestrator.stop()
    logger.info("✓ Task creation and execution test passed")


async def test_task_dependencies():
    """Test task dependency management"""
    logger.info("Testing task dependencies...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Register mock agent
    agent = MockAgent("test_agent", delay=0.1)
    await orchestrator.register_agent(agent)
    
    # Create first task
    task1_id = await orchestrator.create_task(
        agent_id="test_agent",
        task_type="task1",
        payload={"step": 1}
    )
    
    # Create second task that depends on first
    task2_id = await orchestrator.create_task(
        agent_id="test_agent",
        task_type="task2",
        payload={"step": 2},
        dependencies=[task1_id]
    )
    
    # Wait for processing (longer wait for dependency resolution)
    await asyncio.sleep(2.0)
    
    # Check both tasks completed
    task1_status = await orchestrator.get_task_status(task1_id)
    task2_status = await orchestrator.get_task_status(task2_id)
    
    logger.info(f"Task1 status: {task1_status}")
    logger.info(f"Task2 status: {task2_status}")
    
    assert task1_status["status"] == "completed", f"Task1 status: {task1_status['status']}"
    assert task2_status["status"] == "completed", f"Task2 status: {task2_status['status']}"
    
    # Verify execution order (task1 should complete before task2)
    task1_completed = datetime.fromisoformat(task1_status["completed_at"])
    task2_completed = datetime.fromisoformat(task2_status["completed_at"])
    assert task1_completed < task2_completed
    
    await orchestrator.stop()
    logger.info("✓ Task dependencies test passed")


async def test_message_communication():
    """Test inter-agent message communication"""
    logger.info("Testing message communication...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Register mock agents
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    await orchestrator.register_agent(agent1)
    await orchestrator.register_agent(agent2)
    
    # Send message between agents
    message_id = await orchestrator.send_message(
        sender_id="agent1",
        recipient_id="agent2",
        message_type=MessageType.REQUEST,
        payload={"message": "hello from agent1"}
    )
    
    assert message_id is not None
    assert len(orchestrator.message_queue) == 1
    
    # Wait for message processing
    await asyncio.sleep(0.2)
    
    # Message should be delivered
    assert len(orchestrator.message_queue) == 0
    
    await orchestrator.stop()
    logger.info("✓ Message communication test passed")


async def test_context_management():
    """Test shared context management"""
    logger.info("Testing context management...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Register mock agent
    agent = MockAgent("test_agent")
    await orchestrator.register_agent(agent)
    
    # Update shared context
    context_update = {
        "user_profile": {"name": "John Doe", "skills": ["Python", "AI"]},
        "session_id": "test_session_123"
    }
    
    await orchestrator.broadcast_context_update(context_update, "user_session")
    
    # Check context was stored
    context = await orchestrator.get_shared_context("user_session")
    assert context["user_profile"]["name"] == "John Doe"
    assert "Python" in context["user_profile"]["skills"]
    
    await orchestrator.stop()
    logger.info("✓ Context management test passed")


async def test_workflow_coordination():
    """Test complex workflow coordination"""
    logger.info("Testing workflow coordination...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Register mock agents
    agent1 = MockAgent("job_agent", delay=0.1)
    agent2 = MockAgent("skills_agent", delay=0.1)
    agent3 = MockAgent("resume_agent", delay=0.1)
    
    await orchestrator.register_agent(agent1)
    await orchestrator.register_agent(agent2)
    await orchestrator.register_agent(agent3)
    
    # Define workflow
    workflow = {
        "workflow_id": "job_search_workflow",
        "steps": [
            {
                "step_id": "find_jobs",
                "agent_id": "job_agent",
                "task_type": "job_search",
                "task_data": {"query": "Python developer"},
                "dependencies": []
            },
            {
                "step_id": "analyze_skills",
                "agent_id": "skills_agent",
                "task_type": "skill_analysis",
                "task_data": {"user_skills": ["Python", "FastAPI"]},
                "dependencies": ["find_jobs"]
            },
            {
                "step_id": "optimize_resume",
                "agent_id": "resume_agent",
                "task_type": "resume_optimization",
                "task_data": {"target_job": "Python developer"},
                "dependencies": ["analyze_skills"]
            }
        ],
        "timeout": 10
    }
    
    # Execute workflow
    result = await orchestrator.coordinate_agents(workflow)
    
    assert result["success"] == True
    assert "find_jobs" in result["results"]
    assert "analyze_skills" in result["results"]
    assert "optimize_resume" in result["results"]
    
    # Verify all steps completed successfully
    for step_id, step_result in result["results"].items():
        assert step_result["success"] == True
    
    await orchestrator.stop()
    logger.info("✓ Workflow coordination test passed")


async def test_health_monitoring():
    """Test agent health monitoring"""
    logger.info("Testing health monitoring...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Register mock agent
    agent = MockAgent("test_agent")
    await orchestrator.register_agent(agent)
    
    # Get initial health status
    health = orchestrator.agent_health["test_agent"]
    assert health.status == AgentStatus.HEALTHY
    assert health.is_healthy() == True
    
    # Simulate successful task execution
    health.increment_success()
    health.add_response_time(0.5)
    
    assert health.success_count == 1
    assert health.get_success_rate() == 100.0
    
    # Simulate error
    health.increment_error()
    assert health.error_count == 1
    assert health.get_success_rate() == 50.0
    
    await orchestrator.stop()
    logger.info("✓ Health monitoring test passed")


async def test_orchestrator_status():
    """Test orchestrator status reporting"""
    logger.info("Testing orchestrator status...")
    
    orchestrator = AgentOrchestrator()
    await orchestrator.start()
    
    # Register agents and create tasks
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    await orchestrator.register_agent(agent1)
    await orchestrator.register_agent(agent2)
    
    # Create some tasks
    await orchestrator.create_task("agent1", "test", {"data": "test1"})
    await orchestrator.create_task("agent2", "test", {"data": "test2"})
    
    # Get status
    status = await orchestrator.get_orchestrator_status()
    
    assert status["is_running"] == True
    assert status["registered_agents"] == 2
    assert status["queued_tasks"] >= 0
    assert status["max_concurrent_tasks"] > 0
    
    await orchestrator.stop()
    logger.info("✓ Orchestrator status test passed")


async def run_all_tests():
    """Run all orchestrator tests"""
    logger.info("Starting Agent Orchestrator Tests...")
    
    test_functions = [
        test_orchestrator_initialization,
        test_agent_registration,
        test_task_creation_and_execution,
        test_task_dependencies,
        test_message_communication,
        test_context_management,
        test_workflow_coordination,
        test_health_monitoring,
        test_orchestrator_status
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"❌ {test_func.__name__} failed: {str(e)}")
            failed += 1
    
    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed!")
    else:
        logger.error(f"❌ {failed} tests failed")
    
    return failed == 0


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)