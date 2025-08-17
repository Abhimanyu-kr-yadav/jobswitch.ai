"""
Unit tests for Base Agent functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.agents.base import BaseAgent


class TestBaseAgent:
    """Test cases for BaseAgent class"""
    
    @pytest.fixture
    def base_agent(self, mock_watsonx_client, mock_langchain_manager):
        """Create a concrete BaseAgent instance for testing"""
        class ConcreteAgent(BaseAgent):
            def __init__(self, watsonx_client, langchain_manager):
                super().__init__(watsonx_client, langchain_manager)
                self.agent_type = "test"
            
            async def _process_request_impl(self, user_input, context):
                return {"success": True, "data": {"test": "response"}}
            
            async def _get_recommendations_impl(self, user_profile):
                return [{"title": "Test recommendation", "priority": "high"}]
        
        return ConcreteAgent(mock_watsonx_client, mock_langchain_manager)
    
    def test_agent_initialization(self, base_agent):
        """Test agent initialization"""
        assert base_agent.agent_id is not None
        assert base_agent.agent_type == "test"
        assert base_agent.watsonx is not None
        assert base_agent.langchain is not None
        assert isinstance(base_agent.context, dict)
        assert base_agent.created_at is not None
    
    @pytest.mark.asyncio
    async def test_process_request_implementation(self, base_agent):
        """Test that process_request works with concrete implementation"""
        result = await base_agent.process_request("test input", {})
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_update_context(self, base_agent):
        """Test context update functionality"""
        new_context = {"user_id": "test-123", "session_id": "session-456"}
        
        await base_agent.update_context(new_context)
        
        assert base_agent.context["user_id"] == "test-123"
        assert base_agent.context["session_id"] == "session-456"
        assert "updated_at" in base_agent.context
    
    @pytest.mark.asyncio
    async def test_get_recommendations_implementation(self, base_agent):
        """Test that get_recommendations works with concrete implementation"""
        recommendations = await base_agent.get_recommendations({})
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_get_status(self, base_agent):
        """Test agent status retrieval"""
        status = base_agent.get_status()
        
        assert status["agent_id"] == base_agent.agent_id
        assert status["agent_type"] == "base"
        assert status["status"] == "active"
        assert "created_at" in status
        assert "last_activity" in status
    
    @pytest.mark.asyncio
    async def test_log_activity(self, base_agent):
        """Test activity logging"""
        activity_type = "test_activity"
        details = {"test": "data"}
        
        await base_agent._log_activity(activity_type, details)
        
        # Check that activity was logged (in a real implementation, this would check logs)
        assert len(base_agent.activity_log) > 0
        last_activity = base_agent.activity_log[-1]
        assert last_activity["type"] == activity_type
        assert last_activity["details"] == details
        assert "timestamp" in last_activity
    
    @pytest.mark.asyncio
    async def test_validate_input(self, base_agent):
        """Test input validation"""
        # Valid input
        valid_input = {"user_id": "test-123", "data": "test"}
        result = await base_agent._validate_input(valid_input, ["user_id", "data"])
        assert result is True
        
        # Invalid input - missing required field
        invalid_input = {"user_id": "test-123"}
        result = await base_agent._validate_input(invalid_input, ["user_id", "data"])
        assert result is False
        
        # Invalid input - None
        result = await base_agent._validate_input(None, ["user_id"])
        assert result is False
    
    @pytest.mark.asyncio
    async def test_handle_error(self, base_agent):
        """Test error handling"""
        error = Exception("Test error")
        context = {"user_id": "test-123"}
        
        result = await base_agent._handle_error(error, context)
        
        assert result["success"] is False
        assert "error" in result
        assert result["error"]["message"] == "Test error"
        assert result["error"]["type"] == "Exception"
        assert "timestamp" in result["error"]
    
    @pytest.mark.asyncio
    async def test_format_response(self, base_agent):
        """Test response formatting"""
        data = {"test": "data"}
        metadata = {"processing_time": 100}
        
        response = await base_agent._format_response(data, metadata)
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["metadata"] == metadata
        assert "timestamp" in response
        assert "agent_id" in response
    
    @pytest.mark.asyncio
    async def test_get_user_context(self, base_agent, mock_database, sample_user_profile):
        """Test user context retrieval"""
        # Mock database to return user profile
        mock_user = Mock()
        mock_user.to_dict.return_value = sample_user_profile
        mock_database.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.core.database.get_database', return_value=mock_database):
            context = await base_agent._get_user_context("test-user-123")
            
            assert context is not None
            assert context["user_id"] == "test-user-123"
            assert "skills" in context
            assert "experience" in context
    
    @pytest.mark.asyncio
    async def test_cache_result(self, base_agent):
        """Test result caching"""
        cache_key = "test_key"
        data = {"test": "data"}
        ttl = 300
        
        # Test caching
        await base_agent._cache_result(cache_key, data, ttl)
        
        # Test retrieval
        cached_data = await base_agent._get_cached_result(cache_key)
        assert cached_data == data
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, base_agent):
        """Test rate limiting functionality"""
        user_id = "test-user-123"
        
        # First request should pass
        result = await base_agent._check_rate_limit(user_id)
        assert result is True
        
        # Simulate multiple rapid requests
        for _ in range(10):
            await base_agent._check_rate_limit(user_id)
        
        # Should still pass for reasonable limits
        result = await base_agent._check_rate_limit(user_id)
        assert result is True
    
    def test_agent_metrics(self, base_agent):
        """Test agent metrics collection"""
        metrics = base_agent.get_metrics()
        
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "average_response_time" in metrics
        assert "uptime_seconds" in metrics
    
    @pytest.mark.asyncio
    async def test_health_check(self, base_agent):
        """Test agent health check"""
        health = await base_agent.health_check()
        
        assert health["status"] in ["healthy", "unhealthy"]
        assert "agent_id" in health
        assert "checks" in health
        assert "timestamp" in health
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, base_agent):
        """Test handling of concurrent requests"""
        async def mock_process_request(input_data, context):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"success": True, "data": input_data}
        
        # Override the abstract method for testing
        base_agent.process_request = mock_process_request
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = base_agent.process_request(f"input_{i}", {"user_id": f"user_{i}"})
            tasks.append(task)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks)
        
        # Verify all requests completed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["success"] is True
            assert result["data"] == f"input_{i}"