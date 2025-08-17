#!/usr/bin/env python3
"""
Test runner for agent registration integration tests
Provides comprehensive testing of the agent registration flow with detailed reporting
"""
import asyncio
import sys
import time
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentRegistrationTestRunner:
    """Test runner for agent registration integration tests"""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all agent registration integration tests"""
        self.start_time = datetime.utcnow()
        logger.info("Starting agent registration integration test suite...")
        
        try:
            # Import test modules
            from test_agent_registration_flow import TestAgentRegistrationFlow
            
            # Create test instance
            test_instance = TestAgentRegistrationFlow()
            
            # List of test methods to run
            test_methods = [
                'test_orchestrator_initialization_and_readiness',
                'test_wait_for_ready_timeout',
                'test_wait_for_ready_concurrent_waiters',
                'test_successful_agent_registration',
                'test_multiple_agent_registration',
                'test_agent_registration_with_retry_logic',
                'test_agent_registration_failure_after_retries',
                'test_agent_registration_validation',
                'test_orchestrator_not_ready_registration',
                'test_agent_registration_status_tracking',
                'test_get_registered_agents',
                'test_agent_registration_with_real_job_discovery_agent',
                'test_agent_registration_error_handling_and_logging',
                'test_concurrent_agent_registrations',
                'test_agent_registration_performance',
                'test_orchestrator_startup_failure_handling',
                'test_agent_health_status_after_registration',
                'test_registration_status_serialization',
                'test_agent_registration_timeout_scenarios',
                'test_agent_registration_memory_cleanup',
                'test_agent_registration_with_network_simulation',
                'test_agent_registration_race_conditions',
                'test_agent_registration_with_custom_retry_config',
                'test_agent_registration_status_persistence',
                'test_orchestrator_graceful_shutdown_during_registration',
                'test_agent_registration_with_health_check_integration',
                'test_agent_registration_error_recovery'
            ]
            
            # Run each test
            for test_method_name in test_methods:
                await self._run_single_test(test_instance, test_method_name)
            
            self.end_time = datetime.utcnow()
            return self._generate_report()
            
        except Exception as e:
            logger.error(f"Test suite execution failed: {e}")
            self.end_time = datetime.utcnow()
            return self._generate_error_report(str(e))
    
    async def _run_single_test(self, test_instance: Any, test_method_name: str):
        """Run a single test method"""
        logger.info(f"Running test: {test_method_name}")
        test_start = time.time()
        
        try:
            # Get the test method
            test_method = getattr(test_instance, test_method_name)
            
            # Check if test needs orchestrator fixture
            import inspect
            sig = inspect.signature(test_method)
            needs_orchestrator = 'orchestrator' in sig.parameters
            needs_mock_watsonx = 'mock_watsonx_client' in sig.parameters
            needs_caplog = 'caplog' in sig.parameters
            
            # Create fixtures if needed
            kwargs = {}
            orchestrator = None
            
            if needs_orchestrator:
                from app.core.orchestrator import AgentOrchestrator
                orchestrator = AgentOrchestrator()
                await orchestrator.start()
                kwargs['orchestrator'] = orchestrator
            
            if needs_mock_watsonx:
                from unittest.mock import AsyncMock
                mock_client = AsyncMock()
                mock_client.generate_text = AsyncMock(return_value={
                    "success": True,
                    "generated_text": "Mock response"
                })
                kwargs['mock_watsonx_client'] = mock_client
            
            if needs_caplog:
                # Create a simple caplog mock for logging tests
                class MockCaplog:
                    def __init__(self):
                        self.records = []
                    
                    def at_level(self, level):
                        return self
                    
                    def __enter__(self):
                        return self
                    
                    def __exit__(self, *args):
                        pass
                
                kwargs['caplog'] = MockCaplog()
            
            # Run the test
            await test_method(**kwargs)
            
            # Cleanup orchestrator if created
            if orchestrator:
                await orchestrator.stop()
                await asyncio.sleep(0.1)  # Allow cleanup
            
            test_duration = time.time() - test_start
            self.test_results[test_method_name] = {
                'status': 'PASSED',
                'duration': test_duration,
                'error': None
            }
            logger.info(f"✓ {test_method_name} PASSED ({test_duration:.2f}s)")
            
        except Exception as e:
            test_duration = time.time() - test_start
            self.test_results[test_method_name] = {
                'status': 'FAILED',
                'duration': test_duration,
                'error': str(e)
            }
            logger.error(f"✗ {test_method_name} FAILED ({test_duration:.2f}s): {e}")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate test execution report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASSED')
        failed_tests = total_tests - passed_tests
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_duration': total_duration,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            },
            'test_results': self.test_results,
            'failed_tests': {
                name: result for name, result in self.test_results.items()
                if result['status'] == 'FAILED'
            }
        }
        
        return report
    
    def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """Generate error report when test suite fails to run"""
        return {
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'success_rate': 0,
                'total_duration': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
                'error': error_message
            },
            'test_results': {},
            'failed_tests': {}
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted test report"""
        print("\n" + "="*80)
        print("AGENT REGISTRATION INTEGRATION TEST REPORT")
        print("="*80)
        
        summary = report['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        if summary.get('error'):
            print(f"Suite Error: {summary['error']}")
        
        if report['failed_tests']:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for test_name, result in report['failed_tests'].items():
                print(f"✗ {test_name}")
                print(f"  Duration: {result['duration']:.2f}s")
                print(f"  Error: {result['error']}")
                print()
        
        print("\nTEST DETAILS:")
        print("-" * 40)
        for test_name, result in report['test_results'].items():
            status_symbol = "✓" if result['status'] == 'PASSED' else "✗"
            print(f"{status_symbol} {test_name} - {result['status']} ({result['duration']:.2f}s)")
        
        print("="*80)


async def main():
    """Main entry point for test runner"""
    runner = AgentRegistrationTestRunner()
    report = await runner.run_all_tests()
    runner.print_report(report)
    
    # Exit with appropriate code
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())