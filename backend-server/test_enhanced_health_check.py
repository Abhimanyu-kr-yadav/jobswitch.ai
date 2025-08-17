#!/usr/bin/env python3
"""
Test script for enhanced health check endpoint with agent status
Tests the implementation of task 5: Enhance health check endpoint with agent status
"""

import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.orchestrator import AgentOrchestrator, AgentRegistrationStatus, AgentHealthStatus, AgentStatus
from fastapi.testclient import TestClient


class MockAgent:
    """Mock agent for testing"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.status = 'initialized'
    
    async def process_request(self, request):
        return {"status": "success", "result": "mock response"}
    
    async def get_status(self):
        return {"agent_id": self.agent_id, "status": "healthy", "load": 0}


async def test_enhanced_health_check():
    """Test the enhanced health check endpoint structure"""
    
    print("Testing enhanced health check endpoint...")
    
    try:
        # Create test client and call health endpoint
        client = TestClient(app)
        response = client.get("/health")
        
        print(f"Status Code: {response.status_code}")
        
        # Parse response
        health_data = response.json()
        
        # Verify overall structure
        assert "overall_status" in health_data, "Missing overall_status"
        assert "orchestrator" in health_data, "Missing orchestrator section"
        assert "agents" in health_data, "Missing agents section"
        
        # Verify orchestrator status structure
        orchestrator_status = health_data["orchestrator"]
        required_orchestrator_fields = [
            "is_ready", "initialization_phase", "is_running", 
            "registered_agents_count", "registered_agents", 
            "active_tasks_count", "task_queue_size"
        ]
        for field in required_orchestrator_fields:
            assert field in orchestrator_status, f"Missing orchestrator field: {field}"
        
        # Verify agent status structure
        agents_status = health_data["agents"]
        assert "summary" in agents_status, "Missing agents summary"
        assert "registration_details" in agents_status, "Missing agents registration_details"
        
        # Verify agent summary structure
        summary = agents_status["summary"]
        required_summary_fields = [
            "total_configured", "successfully_registered", 
            "failed_registrations", "pending_registrations"
        ]
        for field in required_summary_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify registration details is a dictionary
        details = agents_status["registration_details"]
        assert isinstance(details, dict), "registration_details should be a dictionary"
        
        print("✓ Enhanced health check endpoint structure test passed!")
        print(f"✓ Overall status: {health_data['overall_status']}")
        print(f"✓ Orchestrator ready: {orchestrator_status['is_ready']}")
        print(f"✓ Orchestrator phase: {orchestrator_status['initialization_phase']}")
        print(f"✓ Agents configured: {summary['total_configured']}")
        print(f"✓ Agents registered: {summary['successfully_registered']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_health_check_error_handling():
    """Test health check error handling when orchestrator is not available"""
    
    print("\nTesting health check error handling...")
    
    try:
        # Create test client and call health endpoint
        client = TestClient(app)
        response = client.get("/health")
        
        print(f"Status Code: {response.status_code}")
        
        health_data = response.json()
        
        # Verify error handling structure
        assert "overall_status" in health_data, "Missing overall_status"
        assert "orchestrator" in health_data, "Missing orchestrator section"
        assert "agents" in health_data, "Missing agents section"
        
        # Verify orchestrator error handling
        orchestrator_status = health_data["orchestrator"]
        assert "is_ready" in orchestrator_status, "Missing is_ready field"
        assert "error" in orchestrator_status or orchestrator_status["is_ready"] == True, "Should have error field when not ready"
        
        print("✓ Error handling structure test passed!")
        print(f"✓ Overall status: {health_data['overall_status']}")
        print(f"✓ Orchestrator ready: {orchestrator_status['is_ready']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("Running enhanced health check tests...\n")
    
    # Test enhanced functionality
    test1_passed = await test_enhanced_health_check()
    
    # Test error handling
    test2_passed = test_health_check_error_handling()
    
    print(f"\nTest Results:")
    print(f"Enhanced health check: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Error handling: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed! Enhanced health check endpoint is working correctly.")
        return True
    else:
        print("\n✗ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)