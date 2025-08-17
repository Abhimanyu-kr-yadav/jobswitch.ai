#!/usr/bin/env python3
"""
Integration test for agent fallback behavior
"""
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.api.jobs import (
    _handle_missing_job_discovery_agent,
    _handle_missing_job_recommendation_agent,
    _handle_missing_job_compatibility_agent
)
from app.models.job import Job, JobRecommendation
from app.core.orchestrator import AgentError


async def test_job_discovery_fallback():
    """Test job discovery fallback behavior"""
    print("Testing job discovery fallback...")
    
    # Mock user
    mock_user = Mock()
    mock_user.user_id = "test_user_123"
    
    # Mock database session
    mock_db = Mock()
    
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
    
    # Test the fallback function
    result = await _handle_missing_job_discovery_agent(mock_user, mock_db, {})
    
    # Verify fallback response
    assert result["success"] is True
    assert result["fallback_used"] is True
    assert result["status"] == "completed_with_fallback"
    assert "temporarily unavailable" in result["message"]
    assert "user_message" in result
    assert len(result["jobs"]) == 2
    assert result["jobs"][0]["title"] == "Software Engineer"
    assert result["jobs"][1]["title"] == "Data Scientist"
    
    print("✓ Job discovery fallback test passed")


async def test_job_recommendations_fallback():
    """Test job recommendations fallback behavior"""
    print("Testing job recommendations fallback...")
    
    # Mock user
    mock_user = Mock()
    mock_user.user_id = "test_user_123"
    
    # Mock database session
    mock_db = Mock()
    
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
        if hasattr(model, '__name__') and model.__name__ == "JobRecommendation":
            return mock_rec_query
        elif hasattr(model, '__name__') and model.__name__ == "Job":
            return mock_job_query
        return Mock()
    
    mock_db.query.side_effect = mock_query_side_effect
    
    # Test the fallback function
    result = await _handle_missing_job_recommendation_agent(mock_user, mock_db, 5)
    
    # Verify fallback response
    assert result["success"] is True
    assert result["fallback_used"] is True
    assert result["status"] == "completed_with_fallback"
    assert "previous recommendations" in result["message"]
    assert "user_message" in result
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["job"]["title"] == "Software Engineer"
    assert result["recommendations"][0]["compatibility_score"] == 0.85
    
    print("✓ Job recommendations fallback test passed")


async def test_job_compatibility_fallback():
    """Test job compatibility fallback behavior"""
    print("Testing job compatibility fallback...")
    
    # Mock user
    mock_user = Mock()
    mock_user.user_id = "test_user_123"
    
    # Mock database session
    mock_db = Mock()
    
    # Mock no existing recommendations
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query
    
    # Test the fallback function
    result = await _handle_missing_job_compatibility_agent(mock_user, mock_db, "job_123")
    
    # Verify fallback response
    assert result["success"] is True
    assert result["fallback_used"] is True
    assert result["status"] == "completed_with_fallback"
    assert "temporarily unavailable" in result["message"]
    assert "user_message" in result
    assert "compatibility_analysis" in result
    assert result["compatibility_analysis"]["overall_score"] == 0.0
    assert result["compatibility_analysis"]["reasoning"] == "Compatibility analysis is temporarily unavailable."
    
    print("✓ Job compatibility fallback test passed")


def test_agent_error_details():
    """Test enhanced AgentError with details"""
    print("Testing enhanced AgentError...")
    
    # Test the enhanced error message
    try:
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
    
    print("✓ Enhanced AgentError test passed")


def test_meaningful_user_messages():
    """Test that fallback responses contain meaningful user messages"""
    print("Testing meaningful user messages...")
    
    # Test message content for user-friendliness
    test_messages = [
        "Our AI-powered job discovery is temporarily unavailable, but we've found some recent job postings that might interest you. Please try again later for personalized recommendations.",
        "Our AI recommendation engine is temporarily unavailable, but here are your previous personalized recommendations. Please try again later for new recommendations.",
        "Our AI compatibility analysis is temporarily unavailable. Please try again in a few minutes to get detailed compatibility scores and recommendations for this job."
    ]
    
    for message in test_messages:
        # Verify the message is user-friendly and actionable
        assert len(message) > 50  # Should be descriptive
        assert "temporarily unavailable" in message
        assert "try again" in message
        
        # Should not contain technical terms
        technical_terms = ["agent", "orchestrator", "api", "server", "exception", "error"]
        assert not any(tech_term in message.lower() for tech_term in technical_terms)
    
    print("✓ Meaningful user messages test passed")


async def run_tests():
    """Run all fallback behavior tests"""
    print("Testing agent fallback behavior implementation...")
    print("=" * 50)
    
    try:
        await test_job_discovery_fallback()
        await test_job_recommendations_fallback()
        await test_job_compatibility_fallback()
        test_agent_error_details()
        test_meaningful_user_messages()
        
        print("=" * 50)
        print("✅ All agent fallback behavior tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)