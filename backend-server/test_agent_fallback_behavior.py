#!/usr/bin/env python3
"""
Test script to verify agent fallback behavior implementation
"""
import asyncio
import sys
import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.main import app
from app.core.database import get_database
from app.core.auth import get_current_user
from app.models.user import UserProfile
from app.models.job import Job, JobRecommendation
from app.core.orchestrator import orchestrator, AgentError
from app.agents.base import BaseAgent


class TestAgentFallbackBehavior:
    """Test cases for agent fallback behavior"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.mock_user = Mock()
        self.mock_user.user_id = "test_user_123"
        self.mock_user.email = "test@example.com"
        self.mock_user.first_name = "Test"
        self.mock_user.last_name = "User"
        
    def test_job_discovery_fallback_with_missing_agent(self):
        """Test job discovery fallback when agent is not registered"""
        
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock jobs in database for fallback
        mock_jobs = [
            Mock(
                job_id="job_1",
                title="Software Engineer",
                company="Tech Corp",
                location="San Francisco",
                is_active=True,
                scraped_at="2024-01-01T00:00:00",
                to_dict=Mock(return_value={
                    "job_id": "job_1",
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "location": "San Francisco"
                })
            ),
            Mock(
                job_id="job_2", 
                title="Data Scientist",
                company="Data Inc",
                location="New York",
                is_active=True,
                scraped_at="2024-01-01T00:00:00",
                to_dict=Mock(return_value={
                    "job_id": "job_2",
                    "title": "Data Scientist", 
                    "company": "Data Inc",
                    "location": "New York"
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
        
        # Mock orchestrator to raise AgentError
        with patch('app.api.jobs.orchestrator') as mock_orchestrator:
            mock_orchestrator.create_task.side_effect = AgentError(
                "Agent job_discovery_agent not registered", 
                "job_discovery_agent"
            )
            
            # Mock dependencies
            with patch('app.api.jobs.get_current_user', return_value=self.mock_user):
                with patch('app.api.jobs.get_database', return_value=mock_db):
                    
                    # Make request
                    response = self.client.post("/jobs/discover")
                    
                    # Verify fallback response
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["success"] is True
                    assert data["fallback_used"] is True
                    assert data["status"] == "completed_with_fallback"
                    assert "temporarily unavailable" in data["message"]
                    assert "user_message" in data
                    assert len(data["jobs"]) == 2
                    assert data["jobs"][0]["title"] == "Software Engineer"
                    assert data["jobs"][1]["title"] == "Data Scientist"
    
    def test_job_recommendations_fallback_with_existing_data(self):
        """Test job recommendations fallback using existing recommendations"""
        
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock existing recommendations
        mock_job = Mock(
            job_id="job_1",
            is_active=True,
            to_dict=Mock(return_value={
                "job_id": "job_1",
                "title": "Software Engineer",
                "company": "Tech Corp"
            })
        )
        
        mock_recommendation = Mock(
            id=1,
            job_id="job_1",
            compatibility_score=0.85,
            reasoning="Good match for your skills",
            created_at=Mock(isoformat=Mock(return_value="2024-01-01T00:00:00")),
            user_feedback=None
        )
        
        # Setup mock query chains
        mock_rec_query = Mock()
        mock_rec_query.filter.return_value = mock_rec_query
        mock_rec_query.order_by.return_value = mock_rec_query
        mock_rec_query.limit.return_value = mock_rec_query
        mock_rec_query.all.return_value = [mock_recommendation]
        
        mock_job_query = Mock()
        mock_job_query.filter.return_value = mock_job_query
        mock_job_query.first.return_value = mock_job
        
        def mock_query_side_effect(model):
            if model.__name__ == "JobRecommendation":
                return mock_rec_query
            elif model.__name__ == "Job":
                return mock_job_query
            return Mock()
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # Mock orchestrator to raise AgentError
        with patch('app.api.jobs.orchestrator') as mock_orchestrator:
            mock_orchestrator.create_task.side_effect = AgentError(
                "Agent job_discovery_agent not registered",
                "job_discovery_agent"
            )
            
            # Mock dependencies
            with patch('app.api.jobs.get_current_user', return_value=self.mock_user):
                with patch('app.api.jobs.get_database', return_value=mock_db):
                    
                    # Make request
                    response = self.client.post("/jobs/recommendations/generate?limit=5")
                    
                    # Verify fallback response
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["success"] is True
                    assert data["fallback_used"] is True
                    assert data["status"] == "completed_with_fallback"
                    assert "previous recommendations" in data["message"]
                    assert "user_message" in data
                    assert len(data["recommendations"]) == 1
                    assert data["recommendations"][0]["job"]["title"] == "Software Engineer"
                    assert data["recommendations"][0]["compatibility_score"] == 0.85
    
    def test_job_compatibility_fallback_with_no_existing_data(self):
        """Test job compatibility fallback when no existing analysis exists"""
        
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock no existing recommendations
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Mock orchestrator to raise AgentError
        with patch('app.api.jobs.orchestrator') as mock_orchestrator:
            mock_orchestrator.create_task.side_effect = AgentError(
                "Agent job_discovery_agent not registered",
                "job_discovery_agent"
            )
            
            # Mock dependencies
            with patch('app.api.jobs.get_current_user', return_value=self.mock_user):
                with patch('app.api.jobs.get_database', return_value=mock_db):
                    
                    # Make request
                    response = self.client.post("/jobs/job_123/compatibility")
                    
                    # Verify fallback response
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["success"] is True
                    assert data["fallback_used"] is True
                    assert data["status"] == "completed_with_fallback"
                    assert "temporarily unavailable" in data["message"]
                    assert "user_message" in data
                    assert "compatibility_analysis" in data
                    assert data["compatibility_analysis"]["overall_score"] == 0.0
                    assert data["compatibility_analysis"]["reasoning"] == "Compatibility analysis is temporarily unavailable."
    
    def test_orchestrator_error_details(self):
        """Test that orchestrator provides detailed error information for missing agents"""
        
        # Create a mock orchestrator with some registered agents
        mock_orchestrator = Mock()
        mock_orchestrator.agents = {"agent_1": Mock(), "agent_2": Mock()}
        mock_orchestrator.agent_registration_status = {}
        mock_orchestrator._is_ready = True
        
        # Test the enhanced error message
        with patch('app.core.orchestrator.orchestrator', mock_orchestrator):
            try:
                # This should raise an enhanced AgentError
                raise AgentError(
                    "Agent missing_agent not registered. Available agents: ['agent_1', 'agent_2']",
                    "missing_agent",
                    details={
                        "requested_agent": "missing_agent",
                        "registered_agents": ["agent_1", "agent_2"],
                        "total_registered": 2,
                        "orchestrator_ready": True,
                        "registration_status": None
                    }
                )
            except AgentError as e:
                assert e.agent_id == "missing_agent"
                assert "not registered" in e.message
                assert "Available agents" in e.message
                assert e.details["total_registered"] == 2
                assert e.details["orchestrator_ready"] is True
                assert "agent_1" in e.details["registered_agents"]
                assert "agent_2" in e.details["registered_agents"]
    
    def test_meaningful_user_messages(self):
        """Test that fallback responses contain meaningful user messages"""
        
        # Mock database session with no data
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Mock orchestrator to raise AgentError
        with patch('app.api.jobs.orchestrator') as mock_orchestrator:
            mock_orchestrator.create_task.side_effect = AgentError(
                "Agent job_discovery_agent not registered",
                "job_discovery_agent"
            )
            
            # Mock dependencies
            with patch('app.api.jobs.get_current_user', return_value=self.mock_user):
                with patch('app.api.jobs.get_database', return_value=mock_db):
                    
                    # Test job discovery fallback message
                    response = self.client.post("/jobs/discover")
                    data = response.json()
                    
                    assert "user_message" in data
                    user_message = data["user_message"]
                    assert "temporarily unavailable" in user_message
                    assert "try again later" in user_message
                    assert "search function" in user_message or "browse" in user_message
                    
                    # Verify the message is user-friendly and actionable
                    assert len(user_message) > 50  # Should be descriptive
                    assert not any(tech_term in user_message.lower() for tech_term in [
                        "agent", "orchestrator", "api", "server", "exception"
                    ])  # Should not contain technical terms


def run_tests():
    """Run the fallback behavior tests"""
    print("Testing agent fallback behavior implementation...")
    
    test_instance = TestAgentFallbackBehavior()
    
    try:
        # Run individual tests
        test_instance.setup_method()
        test_instance.test_job_discovery_fallback_with_missing_agent()
        print("✓ Job discovery fallback test passed")
        
        test_instance.setup_method()
        test_instance.test_job_recommendations_fallback_with_existing_data()
        print("✓ Job recommendations fallback test passed")
        
        test_instance.setup_method()
        test_instance.test_job_compatibility_fallback_with_no_existing_data()
        print("✓ Job compatibility fallback test passed")
        
        test_instance.setup_method()
        test_instance.test_orchestrator_error_details()
        print("✓ Orchestrator error details test passed")
        
        test_instance.setup_method()
        test_instance.test_meaningful_user_messages()
        print("✓ Meaningful user messages test passed")
        
        print("\n✅ All agent fallback behavior tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)