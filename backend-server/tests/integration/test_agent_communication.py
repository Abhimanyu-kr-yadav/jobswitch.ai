"""
Integration tests for agent communication and coordination
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.core.orchestrator import AgentOrchestrator
from app.agents.job_discovery import JobDiscoveryAgent
from app.agents.skills_analysis import SkillsAnalysisAgent
from app.agents.resume_optimization import ResumeOptimizationAgent
from app.agents.interview_preparation import InterviewPreparationAgent


class TestAgentCommunication:
    """Test cases for agent communication and coordination"""
    
    @pytest.fixture
    def orchestrator(self, mock_watsonx_client, mock_langchain_manager):
        """Create an orchestrator with mock agents"""
        return AgentOrchestrator(mock_watsonx_client, mock_langchain_manager)
    
    @pytest.fixture
    def mock_agents(self, mock_watsonx_client, mock_langchain_manager):
        """Create mock agent instances"""
        return {
            "job_discovery": JobDiscoveryAgent(mock_watsonx_client, mock_langchain_manager),
            "skills_analysis": SkillsAnalysisAgent(mock_watsonx_client, mock_langchain_manager),
            "resume_optimization": ResumeOptimizationAgent(mock_watsonx_client, mock_langchain_manager),
            "interview_preparation": InterviewPreparationAgent(mock_watsonx_client, mock_langchain_manager)
        }
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.orchestrator_id is not None
        assert orchestrator.watsonx is not None
        assert orchestrator.langchain is not None
        assert isinstance(orchestrator.agents, dict)
        assert isinstance(orchestrator.task_queue, list)
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, orchestrator, mock_agents):
        """Test agent registration with orchestrator"""
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
            
            assert agent_type in orchestrator.agents
            assert orchestrator.agents[agent_type] == agent
    
    @pytest.mark.asyncio
    async def test_cross_agent_workflow(self, orchestrator, mock_agents, sample_user_profile):
        """Test workflow involving multiple agents"""
        # Register agents
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
        
        # Mock agent responses
        with patch.object(mock_agents["job_discovery"], 'process_request') as mock_job_discovery, \
             patch.object(mock_agents["skills_analysis"], 'process_request') as mock_skills_analysis, \
             patch.object(mock_agents["resume_optimization"], 'process_request') as mock_resume_opt:
            
            # Mock responses
            mock_job_discovery.return_value = {
                "success": True,
                "data": {
                    "jobs": [
                        {
                            "job_id": "job-123",
                            "title": "Software Engineer",
                            "requirements": ["Python", "React", "AWS"]
                        }
                    ]
                }
            }
            
            mock_skills_analysis.return_value = {
                "success": True,
                "data": {
                    "critical_gaps": [{"skill": "AWS", "priority": "high"}],
                    "matching_skills": [{"skill": "Python", "match_strength": "strong"}]
                }
            }
            
            mock_resume_opt.return_value = {
                "success": True,
                "data": {
                    "optimized_resume": {"summary": "Updated summary"},
                    "ats_score": 85
                }
            }
            
            # Execute cross-agent workflow
            workflow_data = {
                "user_id": "user-123",
                "workflow_type": "job_application_preparation",
                "target_job_id": "job-123"
            }
            
            result = await orchestrator.execute_workflow(workflow_data)
            
            assert result["success"] is True
            assert "workflow_results" in result["data"]
            
            # Verify all agents were called
            mock_job_discovery.assert_called()
            mock_skills_analysis.assert_called()
            mock_resume_opt.assert_called()
    
    @pytest.mark.asyncio
    async def test_agent_context_sharing(self, orchestrator, mock_agents):
        """Test context sharing between agents"""
        # Register agents
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
        
        # Set shared context
        shared_context = {
            "user_id": "user-123",
            "session_id": "session-456",
            "target_job": {
                "job_id": "job-123",
                "title": "Software Engineer"
            }
        }
        
        await orchestrator.set_shared_context(shared_context)
        
        # Verify context is shared with all agents
        for agent in mock_agents.values():
            agent_context = await agent._get_shared_context()
            assert agent_context["user_id"] == "user-123"
            assert agent_context["session_id"] == "session-456"
    
    @pytest.mark.asyncio
    async def test_task_queue_management(self, orchestrator, mock_agents):
        """Test task queue management and processing"""
        # Register agents
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
        
        # Add tasks to queue
        tasks = [
            {
                "task_id": "task-1",
                "agent_type": "job_discovery",
                "task_data": {"task_type": "discover_jobs", "user_id": "user-123"},
                "priority": "high"
            },
            {
                "task_id": "task-2",
                "agent_type": "skills_analysis",
                "task_data": {"task_type": "analyze_skill_gaps", "user_id": "user-123"},
                "priority": "medium"
            }
        ]
        
        for task in tasks:
            await orchestrator.add_task(task)
        
        assert len(orchestrator.task_queue) == 2
        
        # Process tasks
        with patch.object(mock_agents["job_discovery"], 'process_request') as mock_job_discovery, \
             patch.object(mock_agents["skills_analysis"], 'process_request') as mock_skills_analysis:
            
            mock_job_discovery.return_value = {"success": True, "data": {}}
            mock_skills_analysis.return_value = {"success": True, "data": {}}
            
            results = await orchestrator.process_task_queue()
            
            assert len(results) == 2
            assert all(result["success"] for result in results)
            mock_job_discovery.assert_called_once()
            mock_skills_analysis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, orchestrator, mock_agents):
        """Test handling of agent failures in workflows"""
        # Register agents
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
        
        # Mock one agent to fail
        with patch.object(mock_agents["job_discovery"], 'process_request') as mock_job_discovery, \
             patch.object(mock_agents["skills_analysis"], 'process_request') as mock_skills_analysis:
            
            # Job discovery fails
            mock_job_discovery.side_effect = Exception("Job discovery service unavailable")
            
            # Skills analysis succeeds
            mock_skills_analysis.return_value = {"success": True, "data": {}}
            
            workflow_data = {
                "user_id": "user-123",
                "workflow_type": "job_application_preparation",
                "fallback_enabled": True
            }
            
            result = await orchestrator.execute_workflow(workflow_data)
            
            # Should handle failure gracefully
            assert "errors" in result
            assert len(result["errors"]) > 0
            # Should still complete other agent tasks
            mock_skills_analysis.assert_called()
    
    @pytest.mark.asyncio
    async def test_agent_load_balancing(self, orchestrator):
        """Test load balancing across multiple agent instances"""
        # Create multiple instances of the same agent type
        job_agents = []
        for i in range(3):
            agent = Mock()
            agent.agent_id = f"job_agent_{i}"
            agent.process_request = AsyncMock(return_value={"success": True, "data": {}})
            job_agents.append(agent)
        
        # Register multiple instances
        for i, agent in enumerate(job_agents):
            await orchestrator.register_agent(f"job_discovery_{i}", agent)
        
        # Submit multiple tasks
        tasks = []
        for i in range(6):  # More tasks than agents
            task = {
                "task_id": f"task-{i}",
                "agent_type": "job_discovery",
                "task_data": {"task_type": "discover_jobs", "user_id": f"user-{i}"}
            }
            tasks.append(task)
        
        # Process tasks with load balancing
        results = await orchestrator.process_tasks_with_load_balancing(tasks)
        
        assert len(results) == 6
        # Verify load was distributed across agents
        for agent in job_agents:
            assert agent.process_request.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_real_time_agent_communication(self, orchestrator, mock_agents):
        """Test real-time communication between agents"""
        # Register agents
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
        
        # Set up real-time communication channel
        communication_channel = await orchestrator.create_communication_channel("user-123")
        
        # Mock agent sending message to another agent
        message = {
            "from_agent": "job_discovery",
            "to_agent": "skills_analysis",
            "message_type": "job_requirements",
            "data": {
                "job_id": "job-123",
                "required_skills": ["Python", "React", "AWS"]
            }
        }
        
        # Send message
        await orchestrator.send_agent_message(message)
        
        # Verify message was received
        received_messages = await orchestrator.get_agent_messages("skills_analysis")
        assert len(received_messages) > 0
        assert received_messages[0]["message_type"] == "job_requirements"
    
    @pytest.mark.asyncio
    async def test_agent_health_monitoring(self, orchestrator, mock_agents):
        """Test agent health monitoring and status tracking"""
        # Register agents
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
        
        # Mock health check responses
        for agent in mock_agents.values():
            agent.health_check = AsyncMock(return_value={
                "status": "healthy",
                "response_time_ms": 50,
                "memory_usage_mb": 128,
                "cpu_usage_percent": 25
            })
        
        # Perform health checks
        health_status = await orchestrator.check_all_agents_health()
        
        assert "agents" in health_status
        assert len(health_status["agents"]) == len(mock_agents)
        
        for agent_status in health_status["agents"].values():
            assert agent_status["status"] == "healthy"
            assert "response_time_ms" in agent_status
    
    @pytest.mark.asyncio
    async def test_agent_metrics_aggregation(self, orchestrator, mock_agents):
        """Test aggregation of metrics across agents"""
        # Register agents
        for agent_type, agent in mock_agents.items():
            await orchestrator.register_agent(agent_type, agent)
        
        # Mock metrics from agents
        for agent in mock_agents.values():
            agent.get_metrics = Mock(return_value={
                "total_requests": 100,
                "successful_requests": 95,
                "failed_requests": 5,
                "average_response_time": 250
            })
        
        # Aggregate metrics
        aggregated_metrics = await orchestrator.get_aggregated_metrics()
        
        assert "total_requests" in aggregated_metrics
        assert "success_rate" in aggregated_metrics
        assert "average_response_time" in aggregated_metrics
        assert aggregated_metrics["total_requests"] == 400  # 100 * 4 agents
    
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, orchestrator, mock_database):
        """Test workflow state persistence and recovery"""
        workflow_data = {
            "workflow_id": "workflow-123",
            "user_id": "user-123",
            "workflow_type": "job_application_preparation",
            "current_step": "job_discovery",
            "completed_steps": [],
            "context": {"target_role": "Software Engineer"}
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            # Save workflow state
            await orchestrator.save_workflow_state(workflow_data)
            
            # Verify state was saved
            mock_database.add.assert_called()
            mock_database.commit.assert_called()
            
            # Mock workflow retrieval
            mock_workflow = Mock()
            mock_workflow.to_dict.return_value = workflow_data
            mock_database.query.return_value.filter.return_value.first.return_value = mock_workflow
            
            # Recover workflow state
            recovered_state = await orchestrator.recover_workflow_state("workflow-123")
            
            assert recovered_state["workflow_id"] == "workflow-123"
            assert recovered_state["current_step"] == "job_discovery"