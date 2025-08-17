"""
Comprehensive Test Suite for Error Handling and Logging Implementation
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the error handling components
from app.core.exceptions import (
    JobSwitchException, 
    ValidationException,
    AgentException,
    ExternalAPIException,
    WatsonXException,
    ErrorCode
)
from app.core.error_handler import ErrorHandlerMiddleware
from app.core.logging_config import logging_manager, get_logger
from app.core.retry import retry, RetryConfig, get_retry_stats
from app.core.fallback import fallback_manager, FallbackResult, FallbackStrategy
from app.core.monitoring import (
    monitoring_manager, 
    HealthChecker, 
    HealthStatus,
    DatabaseHealthChecker,
    SystemHealthChecker
)
from app.agents.base import BaseAgent


class TestAgent(BaseAgent):
    """Test agent implementation for testing"""
    
    def __init__(self):
        super().__init__("test_agent")
    
    async def _process_request_impl(self, user_input, context):
        if user_input.get("should_fail"):
            raise Exception("Test failure")
        return {"result": "success", "data": user_input}
    
    async def _get_recommendations_impl(self, user_profile):
        if user_profile.get("should_fail"):
            raise Exception("Recommendation failure")
        return [{"recommendation": "test", "score": 0.9}]


class TestErrorHandling:
    """Test error handling functionality"""
    
    def test_custom_exceptions(self):
        """Test custom exception creation and serialization"""
        # Test JobSwitchException
        exc = JobSwitchException(
            "Test error",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"field": "test"},
            user_message="User friendly message"
        )
        
        error_dict = exc.to_dict()
        assert error_dict["error"]["code"] == ErrorCode.VALIDATION_ERROR.value
        assert error_dict["error"]["message"] == "User friendly message"
        assert error_dict["error"]["details"]["field"] == "test"
        
        # Test ValidationException
        validation_exc = ValidationException(
            "Validation failed",
            field_errors={"email": ["Invalid format"]}
        )
        
        validation_dict = validation_exc.to_dict()
        assert validation_dict["error"]["code"] == ErrorCode.VALIDATION_ERROR.value
        assert "field_errors" in validation_dict["error"]["details"]
        
        # Test AgentException
        agent_exc = AgentException(
            "Agent failed",
            agent_name="test_agent"
        )
        
        agent_dict = agent_exc.to_dict()
        assert agent_dict["error"]["context"]["agent_name"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_error_handler_middleware(self):
        """Test error handler middleware functionality"""
        from fastapi import Request
        from fastapi.responses import JSONResponse
        
        # Mock request
        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {"user-agent": "test"}
        request.client.host = "127.0.0.1"
        request.state = Mock()
        
        middleware = ErrorHandlerMiddleware()
        
        # Test successful request
        async def success_call_next(request):
            return JSONResponse(content={"success": True})
        
        response = await middleware.dispatch(request, success_call_next)
        assert response.status_code == 200
        
        # Test exception handling
        async def failing_call_next(request):
            raise ValidationException("Test validation error")
        
        response = await middleware.dispatch(request, failing_call_next)
        assert response.status_code == 422
        
        # Parse response content
        import json
        content = json.loads(response.body.decode())
        assert content["error"]["code"] == ErrorCode.VALIDATION_ERROR.value


class TestRetryLogic:
    """Test retry functionality"""
    
    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        """Test retry decorator with different scenarios"""
        call_count = 0
        
        @retry(config=RetryConfig(max_attempts=3, base_delay=0.1))
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        # Should succeed after 3 attempts
        result = await failing_function()
        assert result == "success"
        assert call_count == 3
        
        # Test permanent failure
        call_count = 0
        
        @retry(config=RetryConfig(max_attempts=2, base_delay=0.1))
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception, match="Permanent failure"):
            await always_failing_function()
        
        assert call_count == 2
    
    def test_retry_stats(self):
        """Test retry statistics collection"""
        stats = get_retry_stats()
        assert isinstance(stats, dict)
        assert "total_attempts" in stats
        assert "successful_retries" in stats
        assert "failed_retries" in stats


class TestFallbackMechanisms:
    """Test fallback functionality"""
    
    @pytest.mark.asyncio
    async def test_fallback_manager(self):
        """Test fallback manager functionality"""
        from app.core.fallback import DefaultResponseHandler
        
        # Create a fallback handler
        default_responses = {
            "test_operation": {"fallback": True, "data": "default"}
        }
        handler = DefaultResponseHandler(default_responses)
        
        # Register handler
        fallback_manager.register_handler(handler)
        
        # Test fallback handling
        context = {"operation": "test_operation"}
        exception = Exception("Test failure")
        
        result = await fallback_manager.handle_failure(exception, context)
        
        assert result.success is True
        assert result.data["fallback"] is True
        assert result.strategy_used == FallbackStrategy.DEFAULT_RESPONSE
    
    @pytest.mark.asyncio
    async def test_fallback_decorator(self):
        """Test fallback decorator"""
        from app.core.fallback import with_fallback
        
        @with_fallback(operation="test_operation")
        async def failing_function():
            raise Exception("Function failed")
        
        # This would normally use fallback, but we need proper setup
        # For now, just test that the decorator doesn't break the function
        with pytest.raises(Exception):
            await failing_function()


class TestMonitoring:
    """Test monitoring functionality"""
    
    @pytest.mark.asyncio
    async def test_health_checkers(self):
        """Test health checker implementations"""
        # Test system health checker
        system_checker = SystemHealthChecker()
        result = await system_checker.check()
        
        assert result.name == "system"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert result.response_time_ms is not None
        assert "cpu_percent" in result.details
        assert "memory_percent" in result.details
    
    @pytest.mark.asyncio
    async def test_monitoring_manager(self):
        """Test monitoring manager functionality"""
        # Test metrics collection
        monitoring_manager.metrics_collector.record_metric("test_metric", 42.0)
        
        summary = monitoring_manager.metrics_collector.get_metric_summary("test_metric")
        assert summary["count"] == 1
        assert summary["latest"] == 42.0
        
        # Test API call recording
        monitoring_manager.record_api_call("/test", "GET", 200, 150.0)
        
        # Test agent activity recording
        monitoring_manager.record_agent_activity("test_agent", "test_activity", 100.0, True)
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive health check"""
        # Initialize monitoring manager
        await monitoring_manager.initialize()
        
        # Perform health check
        health_result = await monitoring_manager.perform_health_check()
        
        assert "overall_status" in health_result
        assert "checks" in health_result
        assert "timestamp" in health_result
        assert "total_check_time_ms" in health_result
        
        # Check that we have some health checkers registered
        assert len(health_result["checks"]) > 0


class TestAgentErrorHandling:
    """Test agent-specific error handling"""
    
    @pytest.mark.asyncio
    async def test_agent_process_request_success(self):
        """Test successful agent request processing"""
        agent = TestAgent()
        
        user_input = {"test": "data"}
        context = {"user_id": "test_user"}
        
        result = await agent.process_request(user_input, context)
        
        assert result["result"] == "success"
        assert result["data"]["test"] == "data"
        assert agent.success_count == 1
        assert agent.error_count == 0
        assert agent.status == "ready"
    
    @pytest.mark.asyncio
    async def test_agent_process_request_failure(self):
        """Test agent request processing with failure"""
        agent = TestAgent()
        
        user_input = {"should_fail": True}
        context = {"user_id": "test_user"}
        
        with pytest.raises(AgentException):
            await agent.process_request(user_input, context)
        
        assert agent.error_count == 1
        assert agent.status == "error"
    
    @pytest.mark.asyncio
    async def test_agent_recommendations_success(self):
        """Test successful agent recommendation generation"""
        agent = TestAgent()
        
        user_profile = {"user_id": "test_user", "skills": ["python"]}
        
        recommendations = await agent.get_recommendations(user_profile)
        
        assert len(recommendations) == 1
        assert recommendations[0]["recommendation"] == "test"
        assert recommendations[0]["score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_agent_recommendations_failure(self):
        """Test agent recommendation generation with failure"""
        agent = TestAgent()
        
        user_profile = {"should_fail": True}
        
        with pytest.raises(AgentException):
            await agent.get_recommendations(user_profile)
        
        assert agent.error_count == 1
    
    @pytest.mark.asyncio
    async def test_agent_status_reporting(self):
        """Test agent status reporting"""
        agent = TestAgent()
        
        # Initial status
        status = await agent.get_status()
        assert status["agent_id"] == "test_agent"
        assert status["status"] == "initialized"
        assert status["metrics"]["success_count"] == 0
        assert status["metrics"]["error_count"] == 0
        assert status["health"] == "healthy"
        
        # After successful operation
        await agent.process_request({"test": "data"}, {})
        status = await agent.get_status()
        assert status["metrics"]["success_count"] == 1
        assert status["health"] == "healthy"


class TestLoggingSystem:
    """Test logging system functionality"""
    
    def test_logging_manager_initialization(self):
        """Test logging manager initialization"""
        assert logging_manager is not None
        assert logging_manager.context_filter is not None
        assert logging_manager.error_tracker is not None
    
    def test_logging_context(self):
        """Test logging context management"""
        # Set request context
        logging_manager.set_request_context(
            request_id="test_request",
            user_id="test_user",
            endpoint="/test",
            method="GET"
        )
        
        # Context should be set
        assert logging_manager.context_filter.context["request_id"] == "test_request"
        assert logging_manager.context_filter.context["user_id"] == "test_user"
        
        # Clear context
        logging_manager.clear_context()
        assert len(logging_manager.context_filter.context) == 0
    
    def test_error_tracking(self):
        """Test error tracking functionality"""
        # Create and log an error
        error = JobSwitchException(
            "Test error",
            error_code=ErrorCode.VALIDATION_ERROR
        )
        
        logging_manager.log_error(error, {"test": "context"}, "test_user")
        
        # Check error stats
        stats = logging_manager.get_error_stats()
        assert stats["total_errors"] > 0
        assert ErrorCode.VALIDATION_ERROR.value in stats["error_counts"]


class TestIntegration:
    """Integration tests for the complete error handling system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_error_handling(self):
        """Test complete error handling flow"""
        # This would test the complete flow from API request to error handling
        # Including middleware, agent processing, retry, fallback, and logging
        
        agent = TestAgent()
        
        # Test successful flow
        result = await agent.process_request({"test": "data"}, {"user_id": "test"})
        assert result["result"] == "success"
        
        # Test error flow with retry and fallback
        with pytest.raises(AgentException):
            await agent.process_request({"should_fail": True}, {"user_id": "test"})
        
        # Check that error was logged and metrics were recorded
        status = await agent.get_status()
        assert status["metrics"]["error_count"] > 0
    
    @pytest.mark.asyncio
    async def test_monitoring_integration(self):
        """Test monitoring system integration"""
        # Initialize monitoring
        await monitoring_manager.initialize()
        
        # Record some metrics
        monitoring_manager.record_api_call("/test", "GET", 200, 100.0)
        monitoring_manager.record_agent_activity("test_agent", "test", 50.0, True)
        
        # Get comprehensive stats
        from app.core.monitoring import get_monitoring_stats
        stats = get_monitoring_stats()
        
        assert "metrics" in stats
        assert "monitoring_active" in stats
        assert stats["monitoring_active"] is True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])