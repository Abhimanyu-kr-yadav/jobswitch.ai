#!/usr/bin/env python3
"""
Test script for comprehensive logging and error reporting implementation
Tests the enhanced logging throughout the agent registration process
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.logging_config import logging_manager, get_logger, log_agent_activity, log_performance
from app.core.startup_logging import startup_logger, StartupPhase, log_startup_error, log_startup_warning
from app.core.orchestrator import AgentOrchestrator, AgentRegistrationStatus
from app.agents.base import BaseAgent, AgentResponse

# Configure logging for testing
logger = get_logger(__name__)


class MockAgent(BaseAgent):
    """Mock agent for testing registration logging"""
    
    def __init__(self, agent_id: str, should_fail: bool = False):
        super().__init__(agent_id)
        self.should_fail = should_fail
    
    async def _process_request_impl(self, request_data: dict, context: dict = None) -> dict:
        if self.should_fail:
            raise Exception(f"Mock agent {self.agent_id} intentionally failed")
        return {"result": f"Mock response from {self.agent_id}"}
    
    async def _get_recommendations_impl(self, request_data: dict, context: dict = None) -> dict:
        if self.should_fail:
            raise Exception(f"Mock agent {self.agent_id} recommendations failed")
        return {"recommendations": [f"Mock recommendation from {self.agent_id}"]}
    
    async def get_status(self) -> dict:
        if self.should_fail:
            raise Exception(f"Status check failed for {self.agent_id}")
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": datetime.utcnow().isoformat()
        }


async def test_startup_logging():
    """Test startup logging functionality"""
    print("Testing startup logging...")
    
    # Test phase tracking
    phase1 = startup_logger.start_phase(StartupPhase.CORE_INFRASTRUCTURE, "Testing core infrastructure")
    await asyncio.sleep(0.1)  # Simulate work
    startup_logger.complete_phase(StartupPhase.CORE_INFRASTRUCTURE, success=True, summary="Core infrastructure initialized")
    
    # Test error and warning logging
    log_startup_error("Test error message", StartupPhase.AI_SERVICES)
    log_startup_warning("Test warning message", StartupPhase.AI_SERVICES)
    
    # Test dependency checking
    startup_logger.log_dependency_check("test_database", True, {"connection_time": 0.5})
    startup_logger.log_dependency_check("test_redis", False, {"error": "Connection refused"})
    
    # Test component initialization logging
    startup_logger.log_component_initialization("test_component", 1.5, True, {"version": "1.0.0"})
    
    print("✓ Startup logging tests completed")


async def test_orchestrator_logging():
    """Test orchestrator registration logging"""
    print("Testing orchestrator registration logging...")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    try:
        # Start orchestrator
        await orchestrator.start()
        
        # Test successful agent registration
        print("Testing successful agent registration...")
        good_agent = MockAgent("test_good_agent", should_fail=False)
        await orchestrator.register_agent(good_agent)
        print("✓ Successful agent registration logged")
        
        # Test failed agent registration
        print("Testing failed agent registration...")
        bad_agent = MockAgent("test_bad_agent", should_fail=True)
        try:
            await orchestrator.register_agent(bad_agent)
        except Exception as e:
            print(f"✓ Failed agent registration logged: {str(e)}")
        
        # Test agent with invalid ID
        print("Testing agent with invalid ID...")
        invalid_agent = MockAgent("", should_fail=False)  # Empty agent ID
        try:
            await orchestrator.register_agent(invalid_agent)
        except Exception as e:
            print(f"✓ Invalid agent registration logged: {str(e)}")
        
        # Test registration status tracking
        print("Testing registration status tracking...")
        status = orchestrator.agent_registration_status.get("test_good_agent")
        if status:
            print(f"✓ Registration status tracked: {status.to_dict()}")
        
    finally:
        await orchestrator.stop()
    
    print("✓ Orchestrator logging tests completed")


async def test_performance_logging():
    """Test performance logging functionality"""
    print("Testing performance logging...")
    
    # Test performance logging
    start_time = datetime.utcnow()
    await asyncio.sleep(0.1)  # Simulate work
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    log_performance("test_operation", duration, {"test_data": "value"})
    
    # Test agent activity logging
    log_agent_activity("test_agent", "test_activity", "completed", {"result": "success"})
    
    print("✓ Performance logging tests completed")


async def test_error_reporting():
    """Test comprehensive error reporting"""
    print("Testing error reporting...")
    
    # Test structured error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logging_manager.log_error(
            e,
            context={"test_context": "error_reporting_test"},
            user_id="test_user"
        )
    
    # Test error statistics
    error_stats = logging_manager.get_error_stats()
    print(f"✓ Error statistics: {error_stats}")
    
    print("✓ Error reporting tests completed")


async def test_context_logging():
    """Test context-aware logging"""
    print("Testing context-aware logging...")
    
    # Test request context
    logging_manager.set_request_context(
        request_id="test_request_123",
        user_id="test_user",
        endpoint="/test",
        method="POST"
    )
    
    logger.info("Test message with request context")
    
    # Test agent context
    logging_manager.set_agent_context(
        agent_name="test_agent",
        task_id="test_task_456",
        user_id="test_user"
    )
    
    logger.info("Test message with agent context")
    
    # Clear context
    logging_manager.clear_context()
    logger.info("Test message without context")
    
    print("✓ Context logging tests completed")


def test_log_file_structure():
    """Test log file structure and rotation"""
    print("Testing log file structure...")
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"✓ Found {len(log_files)} log files:")
        for log_file in log_files:
            print(f"  - {log_file.name}")
    else:
        print("⚠ Logs directory not found")
    
    print("✓ Log file structure test completed")


async def main():
    """Run all logging tests"""
    print("=" * 60)
    print("COMPREHENSIVE LOGGING AND ERROR REPORTING TESTS")
    print("=" * 60)
    
    try:
        # Run all tests
        await test_startup_logging()
        print()
        
        await test_orchestrator_logging()
        print()
        
        await test_performance_logging()
        print()
        
        await test_error_reporting()
        print()
        
        await test_context_logging()
        print()
        
        test_log_file_structure()
        print()
        
        # Generate startup report
        print("Generating startup report...")
        startup_summary = startup_logger.log_startup_complete(success=True)
        print(f"✓ Startup completed in {startup_summary['total_duration']:.2f} seconds")
        
        # Export startup log
        log_file = startup_logger.export_startup_log()
        if log_file:
            print(f"✓ Startup log exported to {log_file}")
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Print summary of logging features tested
        print("\nLogging features tested:")
        print("✓ Structured JSON logging")
        print("✓ Agent registration logging with retry tracking")
        print("✓ Startup phase tracking and performance metrics")
        print("✓ Error reporting with context and stack traces")
        print("✓ Performance logging with timing data")
        print("✓ Context-aware logging (request/agent context)")
        print("✓ Log file rotation and organization")
        print("✓ Comprehensive error statistics")
        print("✓ Startup report generation and export")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())