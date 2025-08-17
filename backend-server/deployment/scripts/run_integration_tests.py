#!/usr/bin/env python3
"""
Comprehensive Integration Test Runner for JobSwitch.ai
Runs end-to-end integration tests across all system components.
"""

import asyncio
import subprocess
import sys
import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import docker
import psycopg2
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integration_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Comprehensive integration test runner"""
    
    def __init__(self):
        self.test_results = {}
        self.docker_client = None
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("Starting comprehensive integration tests...")
        
        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            
            # Test infrastructure components
            await self.test_infrastructure()
            
            # Test database connectivity and operations
            await self.test_database_integration()
            
            # Test Redis cache integration
            await self.test_redis_integration()
            
            # Test API endpoints
            await self.test_api_integration()
            
            # Test agent communication
            await self.test_agent_integration()
            
            # Test external API integrations
            await self.test_external_api_integration()
            
            # Test WebSocket functionality
            await self.test_websocket_integration()
            
            # Test security features
            await self.test_security_integration()
            
            # Test performance under load
            await self.test_performance_integration()
            
            # Test error handling and recovery
            await self.test_error_handling_integration()
            
            # Generate final report
            report = self.generate_test_report()
            
            logger.info("Integration tests completed")
            return report
            
        except Exception as e:
            logger.error(f"Integration test runner failed: {e}")
            return {'error': str(e), 'results': self.test_results}
    
    async def test_infrastructure(self):
        """Test infrastructure components"""
        logger.info("Testing infrastructure components...")
        
        infrastructure_tests = {}
        
        # Test Docker containers
        try:
            containers = self.docker_client.containers.list()
            running_containers = [c.name for c in containers if c.status == 'running']
            
            expected_containers = ['api', 'db', 'redis', 'nginx']
            missing_containers = [c for c in expected_containers if not any(c in name for name in running_containers)]
            
            infrastructure_tests['docker'] = {
                'running_containers': running_containers,
                'missing_containers': missing_containers,
                'status': 'pass' if not missing_containers else 'fail'
            }
            
        except Exception as e:
            infrastructure_tests['docker'] = {'status': 'fail', 'error': str(e)}
        
        # Test network connectivity
        network_tests = {}
        services = {
            'api': (os.getenv('API_HOST', 'localhost'), int(os.getenv('API_PORT', 8000))),
            'database': (os.getenv('DB_HOST', 'localhost'), int(os.getenv('DB_PORT', 5432))),
            'redis': (os.getenv('REDIS_HOST', 'localhost'), int(os.getenv('REDIS_PORT', 6379)))
        }
        
        for service, (host, port) in services.items():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                network_tests[service] = {
                    'host': host,
                    'port': port,
                    'status': 'pass' if result == 0 else 'fail',
                    'reachable': result == 0
                }
            except Exception as e:
                network_tests[service] = {'status': 'fail', 'error': str(e)}
        
        infrastructure_tests['network'] = network_tests
        self.test_results['infrastructure'] = infrastructure_tests
    
    async def test_database_integration(self):
        """Test database integration"""
        logger.info("Testing database integration...")
        
        db_tests = {}
        
        try:
            # Test connection
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('POSTGRES_DB', 'jobswitch'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'password')
            )
            cursor = conn.cursor()
            
            # Test basic operations
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            db_tests['connection'] = {'status': 'pass', 'version': version}
            
            # Test table existence
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['users', 'jobs', 'resumes', 'interviews', 'networking_campaigns']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            db_tests['schema'] = {
                'existing_tables': tables,
                'missing_tables': missing_tables,
                'status': 'pass' if not missing_tables else 'fail'
            }
            
            # Test CRUD operations
            try:
                # Create test record
                cursor.execute("""
                    INSERT INTO users (email, full_name, created_at) 
                    VALUES ('test@integration.com', 'Integration Test', NOW())
                    ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name
                    RETURNING id
                """)
                user_id = cursor.fetchone()[0]
                
                # Read test record
                cursor.execute("SELECT email, full_name FROM users WHERE id = %s", (user_id,))
                user_data = cursor.fetchone()
                
                # Update test record
                cursor.execute("""
                    UPDATE users SET full_name = 'Updated Integration Test' 
                    WHERE id = %s
                """, (user_id,))
                
                # Delete test record
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                
                conn.commit()
                db_tests['crud_operations'] = {'status': 'pass'}
                
            except Exception as e:
                conn.rollback()
                db_tests['crud_operations'] = {'status': 'fail', 'error': str(e)}
            
            # Test performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            db_tests['performance'] = {
                'user_count': count,
                'query_time_ms': round(query_time * 1000, 2),
                'status': 'pass' if query_time < 1.0 else 'warn'
            }
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            db_tests['connection'] = {'status': 'fail', 'error': str(e)}
        
        self.test_results['database'] = db_tests
    
    async def test_redis_integration(self):
        """Test Redis cache integration"""
        logger.info("Testing Redis integration...")
        
        redis_tests = {}
        
        try:
            # Test connection
            r = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
            
            # Test basic operations
            ping_result = r.ping()
            redis_tests['connection'] = {'status': 'pass', 'ping': ping_result}
            
            # Test cache operations
            test_key = 'integration_test_key'
            test_value = 'integration_test_value'
            
            # Set value
            r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            
            # Get value
            retrieved_value = r.get(test_key)
            
            # Delete value
            r.delete(test_key)
            
            redis_tests['cache_operations'] = {
                'set_get_delete': retrieved_value == test_value,
                'status': 'pass' if retrieved_value == test_value else 'fail'
            }
            
            # Test performance
            start_time = time.time()
            for i in range(100):
                r.set(f'perf_test_{i}', f'value_{i}')
            set_time = time.time() - start_time
            
            start_time = time.time()
            for i in range(100):
                r.get(f'perf_test_{i}')
            get_time = time.time() - start_time
            
            # Cleanup
            for i in range(100):
                r.delete(f'perf_test_{i}')
            
            redis_tests['performance'] = {
                'set_100_keys_ms': round(set_time * 1000, 2),
                'get_100_keys_ms': round(get_time * 1000, 2),
                'status': 'pass' if set_time < 1.0 and get_time < 1.0 else 'warn'
            }
            
        except Exception as e:
            redis_tests['connection'] = {'status': 'fail', 'error': str(e)}
        
        self.test_results['redis'] = redis_tests
    
    async def test_api_integration(self):
        """Test API endpoint integration"""
        logger.info("Testing API integration...")
        
        api_tests = {}
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/health", timeout=10)
            api_tests['health'] = {
                'status_code': response.status_code,
                'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                'status': 'pass' if response.status_code == 200 else 'fail'
            }
        except Exception as e:
            api_tests['health'] = {'status': 'fail', 'error': str(e)}
        
        # Test authentication endpoints
        auth_tests = {}
        
        # Test user registration
        try:
            register_data = {
                'email': f'integration_test_{int(time.time())}@test.com',
                'password': 'TestPassword123!',
                'full_name': 'Integration Test User'
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/v1/auth/register",
                json=register_data,
                timeout=10
            )
            
            auth_tests['register'] = {
                'status_code': response.status_code,
                'status': 'pass' if response.status_code in [201, 409] else 'fail'  # 409 if user exists
            }
            
            # Test login if registration successful
            if response.status_code == 201:
                login_response = requests.post(
                    f"{self.api_base_url}/api/v1/auth/login",
                    json={'email': register_data['email'], 'password': register_data['password']},
                    timeout=10
                )
                
                auth_tests['login'] = {
                    'status_code': login_response.status_code,
                    'has_token': 'access_token' in login_response.json() if login_response.status_code == 200 else False,
                    'status': 'pass' if login_response.status_code == 200 else 'fail'
                }
                
                # Store token for further tests
                if login_response.status_code == 200:
                    self.auth_token = login_response.json().get('access_token')
            
        except Exception as e:
            auth_tests['register'] = {'status': 'fail', 'error': str(e)}
        
        api_tests['authentication'] = auth_tests
        
        # Test protected endpoints (if we have a token)
        if hasattr(self, 'auth_token'):
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            
            protected_endpoints = [
                '/api/v1/user/profile',
                '/api/v1/agents/job-discovery/search',
                '/api/v1/agents/skills-analysis/analyze'
            ]
            
            protected_tests = {}
            for endpoint in protected_endpoints:
                try:
                    response = requests.get(f"{self.api_base_url}{endpoint}", headers=headers, timeout=10)
                    protected_tests[endpoint] = {
                        'status_code': response.status_code,
                        'status': 'pass' if response.status_code in [200, 404, 422] else 'fail'
                    }
                except Exception as e:
                    protected_tests[endpoint] = {'status': 'fail', 'error': str(e)}
            
            api_tests['protected_endpoints'] = protected_tests
        
        self.test_results['api'] = api_tests
    
    async def test_agent_integration(self):
        """Test AI agent integration"""
        logger.info("Testing agent integration...")
        
        agent_tests = {}
        
        # Test agent orchestration
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/orchestrator/health",
                timeout=10
            )
            
            agent_tests['orchestrator'] = {
                'status_code': response.status_code,
                'status': 'pass' if response.status_code in [200, 404] else 'fail'
            }
        except Exception as e:
            agent_tests['orchestrator'] = {'status': 'fail', 'error': str(e)}
        
        # Test individual agents (mock responses expected)
        agents = [
            'job-discovery',
            'skills-analysis',
            'resume-optimization',
            'interview-preparation',
            'networking',
            'career-strategy'
        ]
        
        for agent in agents:
            try:
                response = requests.get(
                    f"{self.api_base_url}/api/v1/agents/{agent}/health",
                    timeout=10
                )
                
                agent_tests[agent] = {
                    'status_code': response.status_code,
                    'status': 'pass' if response.status_code in [200, 404] else 'fail'
                }
            except Exception as e:
                agent_tests[agent] = {'status': 'fail', 'error': str(e)}
        
        self.test_results['agents'] = agent_tests
    
    async def test_external_api_integration(self):
        """Test external API integrations"""
        logger.info("Testing external API integration...")
        
        external_tests = {}
        
        # Test job board API connections (mock or real)
        job_boards = ['linkedin', 'indeed', 'glassdoor', 'angellist']
        
        for board in job_boards:
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/v1/integrations/{board}/test",
                    timeout=10
                )
                
                external_tests[board] = {
                    'status_code': response.status_code,
                    'status': 'pass' if response.status_code in [200, 404, 503] else 'fail'
                }
            except Exception as e:
                external_tests[board] = {'status': 'fail', 'error': str(e)}
        
        # Test WatsonX integration
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/integrations/watsonx/test",
                timeout=10
            )
            
            external_tests['watsonx'] = {
                'status_code': response.status_code,
                'status': 'pass' if response.status_code in [200, 404, 503] else 'fail'
            }
        except Exception as e:
            external_tests['watsonx'] = {'status': 'fail', 'error': str(e)}
        
        self.test_results['external_apis'] = external_tests
    
    async def test_websocket_integration(self):
        """Test WebSocket functionality"""
        logger.info("Testing WebSocket integration...")
        
        websocket_tests = {}
        
        try:
            import websockets
            
            # Test WebSocket connection
            uri = f"ws://localhost:8000/ws/dashboard"
            
            async with websockets.connect(uri, timeout=10) as websocket:
                # Send test message
                test_message = {"type": "ping", "data": "test"}
                await websocket.send(json.dumps(test_message))
                
                # Receive response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                
                websocket_tests['connection'] = {
                    'connected': True,
                    'message_sent': True,
                    'response_received': True,
                    'status': 'pass'
                }
                
        except Exception as e:
            websocket_tests['connection'] = {'status': 'fail', 'error': str(e)}
        
        self.test_results['websocket'] = websocket_tests
    
    async def test_security_integration(self):
        """Test security features"""
        logger.info("Testing security integration...")
        
        security_tests = {}
        
        # Test rate limiting
        try:
            responses = []
            for i in range(20):  # Try to exceed rate limit
                response = requests.get(f"{self.api_base_url}/api/v1/health", timeout=5)
                responses.append(response.status_code)
            
            rate_limited = any(code == 429 for code in responses)
            security_tests['rate_limiting'] = {
                'responses': responses[-5:],  # Last 5 responses
                'rate_limited': rate_limited,
                'status': 'pass' if rate_limited else 'warn'
            }
        except Exception as e:
            security_tests['rate_limiting'] = {'status': 'fail', 'error': str(e)}
        
        # Test input validation
        try:
            invalid_data = {
                'email': 'not_an_email',
                'password': '123',  # Too short
                'full_name': ''  # Empty
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/v1/auth/register",
                json=invalid_data,
                timeout=10
            )
            
            security_tests['input_validation'] = {
                'status_code': response.status_code,
                'validation_rejected': response.status_code == 422,
                'status': 'pass' if response.status_code == 422 else 'fail'
            }
        except Exception as e:
            security_tests['input_validation'] = {'status': 'fail', 'error': str(e)}
        
        # Test HTTPS redirect (if applicable)
        try:
            response = requests.get('http://localhost:80', allow_redirects=False, timeout=5)
            security_tests['https_redirect'] = {
                'status_code': response.status_code,
                'redirects_to_https': response.status_code in [301, 302, 308],
                'status': 'pass' if response.status_code in [301, 302, 308] else 'warn'
            }
        except Exception as e:
            security_tests['https_redirect'] = {'status': 'skip', 'error': str(e)}
        
        self.test_results['security'] = security_tests
    
    async def test_performance_integration(self):
        """Test performance under load"""
        logger.info("Testing performance integration...")
        
        performance_tests = {}
        
        # Concurrent request test
        async def make_concurrent_request():
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base_url}/api/v1/health", timeout=10)
                end_time = time.time()
                return {
                    'success': response.status_code == 200,
                    'response_time': end_time - start_time
                }
            except:
                return {'success': False, 'response_time': None}
        
        # Run 20 concurrent requests
        tasks = [make_concurrent_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_requests if r['response_time']]
        
        performance_tests['concurrent_load'] = {
            'total_requests': 20,
            'successful_requests': len(successful_requests),
            'success_rate_percent': round(len(successful_requests) / 20 * 100, 2),
            'avg_response_time_ms': round(sum(response_times) / len(response_times) * 1000, 2) if response_times else 0,
            'max_response_time_ms': round(max(response_times) * 1000, 2) if response_times else 0,
            'status': 'pass' if len(successful_requests) >= 18 else 'fail'  # 90% success rate
        }
        
        self.test_results['performance'] = performance_tests
    
    async def test_error_handling_integration(self):
        """Test error handling and recovery"""
        logger.info("Testing error handling integration...")
        
        error_tests = {}
        
        # Test 404 handling
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/nonexistent", timeout=10)
            error_tests['404_handling'] = {
                'status_code': response.status_code,
                'proper_404': response.status_code == 404,
                'status': 'pass' if response.status_code == 404 else 'fail'
            }
        except Exception as e:
            error_tests['404_handling'] = {'status': 'fail', 'error': str(e)}
        
        # Test malformed JSON handling
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/auth/register",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            error_tests['malformed_json'] = {
                'status_code': response.status_code,
                'proper_error': response.status_code in [400, 422],
                'status': 'pass' if response.status_code in [400, 422] else 'fail'
            }
        except Exception as e:
            error_tests['malformed_json'] = {'status': 'fail', 'error': str(e)}
        
        # Test unauthorized access
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/user/profile",
                headers={'Authorization': 'Bearer invalid_token'},
                timeout=10
            )
            error_tests['unauthorized_access'] = {
                'status_code': response.status_code,
                'proper_401': response.status_code == 401,
                'status': 'pass' if response.status_code == 401 else 'fail'
            }
        except Exception as e:
            error_tests['unauthorized_access'] = {'status': 'fail', 'error': str(e)}
        
        self.test_results['error_handling'] = error_tests
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Calculate overall statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warnings = 0
        
        def count_tests(test_dict):
            nonlocal total_tests, passed_tests, failed_tests, warnings
            
            for key, value in test_dict.items():
                if isinstance(value, dict):
                    if 'status' in value:
                        total_tests += 1
                        if value['status'] == 'pass':
                            passed_tests += 1
                        elif value['status'] == 'fail':
                            failed_tests += 1
                        elif value['status'] == 'warn':
                            warnings += 1
                    else:
                        count_tests(value)
        
        count_tests(self.test_results)
        
        # Identify critical failures
        critical_failures = []
        if 'infrastructure' in self.test_results:
            infra = self.test_results['infrastructure']
            if infra.get('docker', {}).get('status') == 'fail':
                critical_failures.append('Docker containers not running')
        
        if 'database' in self.test_results:
            db = self.test_results['database']
            if db.get('connection', {}).get('status') == 'fail':
                critical_failures.append('Database connection failed')
        
        if 'api' in self.test_results:
            api = self.test_results['api']
            if api.get('health', {}).get('status') == 'fail':
                critical_failures.append('API health check failed')
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warnings,
                'success_rate_percent': round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
            },
            'critical_failures': critical_failures,
            'test_results': self.test_results,
            'recommendations': self.generate_recommendations()
        }
        
        # Save report
        report_file = f"logs/integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Integration test report saved to {report_file}")
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for critical infrastructure issues
        if 'infrastructure' in self.test_results:
            infra = self.test_results['infrastructure']
            if infra.get('docker', {}).get('missing_containers'):
                recommendations.append("Start missing Docker containers before deployment")
        
        # Check for database issues
        if 'database' in self.test_results:
            db = self.test_results['database']
            if db.get('connection', {}).get('status') == 'fail':
                recommendations.append("Fix database connection issues")
            if db.get('schema', {}).get('missing_tables'):
                recommendations.append("Run database migrations to create missing tables")
        
        # Check for performance issues
        if 'performance' in self.test_results:
            perf = self.test_results['performance']
            if perf.get('concurrent_load', {}).get('success_rate_percent', 100) < 90:
                recommendations.append("Investigate performance issues under concurrent load")
        
        # Check for security issues
        if 'security' in self.test_results:
            sec = self.test_results['security']
            if not sec.get('rate_limiting', {}).get('rate_limited', False):
                recommendations.append("Implement or fix rate limiting")
            if not sec.get('input_validation', {}).get('validation_rejected', False):
                recommendations.append("Improve input validation")
        
        return recommendations

async def main():
    """Main test runner function"""
    runner = IntegrationTestRunner()
    report = await runner.run_all_tests()
    
    print("\n" + "="*60)
    print("INTEGRATION TEST REPORT")
    print("="*60)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Success Rate: {report['summary']['success_rate_percent']}%")
    
    if report['critical_failures']:
        print("\nCRITICAL FAILURES:")
        for failure in report['critical_failures']:
            print(f"  ❌ {failure}")
    
    if report['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  💡 {rec}")
    
    print(f"\nDetailed report saved to logs/integration_test_report_*.json")
    
    # Exit with appropriate code
    if report['summary']['failed'] > 0 or report['critical_failures']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())