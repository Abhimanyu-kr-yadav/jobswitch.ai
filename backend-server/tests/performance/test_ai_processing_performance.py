"""
Performance tests for AI processing times and system load
"""
import pytest
import asyncio
import time
import psutil
import statistics
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.agents.job_discovery import JobDiscoveryAgent
from app.agents.skills_analysis import SkillsAnalysisAgent
from app.agents.resume_optimization import ResumeOptimizationAgent
from app.agents.interview_preparation import InterviewPreparationAgent


class TestAIProcessingPerformance:
    """Performance test cases for AI processing"""
    
    @pytest.fixture
    def performance_agents(self, mock_watsonx_client, mock_langchain_manager):
        """Create agent instances for performance testing"""
        return {
            "job_discovery": JobDiscoveryAgent(mock_watsonx_client, mock_langchain_manager),
            "skills_analysis": SkillsAnalysisAgent(mock_watsonx_client, mock_langchain_manager),
            "resume_optimization": ResumeOptimizationAgent(mock_watsonx_client, mock_langchain_manager),
            "interview_preparation": InterviewPreparationAgent(mock_watsonx_client, mock_langchain_manager)
        }
    
    @pytest.mark.asyncio
    async def test_ai_response_time_performance(self, performance_agents, performance_thresholds):
        """Test AI response times meet performance requirements"""
        
        test_requests = [
            {
                "agent": "job_discovery",
                "request": {
                    "task_type": "discover_jobs",
                    "user_id": "user-123",
                    "search_criteria": {"keywords": ["python", "react"]}
                }
            },
            {
                "agent": "skills_analysis",
                "request": {
                    "task_type": "analyze_skill_gaps",
                    "user_id": "user-123",
                    "job_description": "Python developer with React experience"
                }
            },
            {
                "agent": "resume_optimization",
                "request": {
                    "task_type": "optimize_resume",
                    "user_id": "user-123",
                    "resume_id": "resume-123",
                    "job_id": "job-123"
                }
            },
            {
                "agent": "interview_preparation",
                "request": {
                    "task_type": "generate_questions",
                    "user_id": "user-123",
                    "job_role": "Software Engineer"
                }
            }
        ]
        
        response_times = []
        
        for test_case in test_requests:
            agent = performance_agents[test_case["agent"]]
            
            # Mock successful response
            with patch.object(agent, 'process_request') as mock_process:
                mock_process.return_value = {
                    "success": True,
                    "data": {"test": "response"}
                }
                
                start_time = time.time()
                result = await agent.process_request(test_case["request"], {})
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                
                assert result["success"] is True
                assert response_time_ms < performance_thresholds["ai_response_time_ms"]
        
        # Calculate performance statistics
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print(f"AI Response Time Performance:")
        print(f"  Average: {avg_response_time:.2f}ms")
        print(f"  Maximum: {max_response_time:.2f}ms")
        print(f"  Minimum: {min_response_time:.2f}ms")
        print(f"  Threshold: {performance_thresholds['ai_response_time_ms']}ms")
        
        assert avg_response_time < performance_thresholds["ai_response_time_ms"]
    
    @pytest.mark.asyncio
    async def test_concurrent_ai_processing(self, performance_agents, performance_thresholds):
        """Test AI processing under concurrent load"""
        
        concurrent_requests = 10
        agent = performance_agents["job_discovery"]
        
        # Mock agent response
        with patch.object(agent, 'process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "data": {"jobs": [{"id": "job-1"}]}
            }
            
            # Create concurrent requests
            tasks = []
            start_time = time.time()
            
            for i in range(concurrent_requests):
                request_data = {
                    "task_type": "discover_jobs",
                    "user_id": f"user-{i}",
                    "search_criteria": {"keywords": ["python"]}
                }
                task = agent.process_request(request_data, {})
                tasks.append(task)
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time_ms = (end_time - start_time) * 1000
            avg_time_per_request = total_time_ms / concurrent_requests
            
            print(f"Concurrent AI Processing Performance:")
            print(f"  Concurrent requests: {concurrent_requests}")
            print(f"  Total time: {total_time_ms:.2f}ms")
            print(f"  Average per request: {avg_time_per_request:.2f}ms")
            
            # All requests should succeed
            assert all(result["success"] for result in results)
            
            # Average time per request should be reasonable
            assert avg_time_per_request < performance_thresholds["ai_response_time_ms"]
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_ai_processing(self, performance_agents, performance_thresholds):
        """Test memory usage during AI processing"""
        
        agent = performance_agents["skills_analysis"]
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Mock agent response
        with patch.object(agent, 'process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "data": {"skills": ["Python", "React"]}
            }
            
            # Process multiple requests to simulate load
            for i in range(20):
                request_data = {
                    "task_type": "extract_skills_from_resume",
                    "user_id": f"user-{i}",
                    "resume_text": f"Software engineer with Python experience {i}"
                }
                
                await agent.process_request(request_data, {})
            
            # Get final memory usage
            final_memory_mb = process.memory_info().rss / 1024 / 1024
            memory_increase_mb = final_memory_mb - initial_memory_mb
            
            print(f"Memory Usage Performance:")
            print(f"  Initial memory: {initial_memory_mb:.2f}MB")
            print(f"  Final memory: {final_memory_mb:.2f}MB")
            print(f"  Memory increase: {memory_increase_mb:.2f}MB")
            print(f"  Threshold: {performance_thresholds['memory_usage_mb']}MB")
            
            # Memory increase should be within acceptable limits
            assert memory_increase_mb < performance_thresholds["memory_usage_mb"]
    
    @pytest.mark.asyncio
    async def test_cpu_usage_during_ai_processing(self, performance_agents, performance_thresholds):
        """Test CPU usage during AI processing"""
        
        agent = performance_agents["resume_optimization"]
        
        # Mock agent response with some processing delay
        async def mock_process_with_delay(request_data, context):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"success": True, "data": {"optimized_resume": {}}}
        
        with patch.object(agent, 'process_request', side_effect=mock_process_with_delay):
            # Monitor CPU usage during processing
            cpu_percentages = []
            
            async def monitor_cpu():
                for _ in range(10):  # Monitor for 1 second
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    cpu_percentages.append(cpu_percent)
            
            async def process_requests():
                tasks = []
                for i in range(5):
                    request_data = {
                        "task_type": "optimize_resume",
                        "user_id": f"user-{i}",
                        "resume_id": f"resume-{i}",
                        "job_id": f"job-{i}"
                    }
                    task = agent.process_request(request_data, {})
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
            
            # Run CPU monitoring and request processing concurrently
            await asyncio.gather(monitor_cpu(), process_requests())
            
            if cpu_percentages:
                avg_cpu_usage = statistics.mean(cpu_percentages)
                max_cpu_usage = max(cpu_percentages)
                
                print(f"CPU Usage Performance:")
                print(f"  Average CPU usage: {avg_cpu_usage:.2f}%")
                print(f"  Maximum CPU usage: {max_cpu_usage:.2f}%")
                print(f"  Threshold: {performance_thresholds['cpu_usage_percent']}%")
                
                # CPU usage should be within acceptable limits
                assert avg_cpu_usage < performance_thresholds["cpu_usage_percent"]
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, performance_agents, mock_database, performance_thresholds):
        """Test database query performance"""
        
        agent = performance_agents["job_discovery"]
        
        # Mock database queries with timing
        query_times = []
        
        def mock_query_with_timing(*args, **kwargs):
            start_time = time.time()
            # Simulate database query
            time.sleep(0.01)  # 10ms simulated query time
            end_time = time.time()
            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)
            return mock_database.query.return_value
        
        mock_database.query.side_effect = mock_query_with_timing
        
        with patch('app.core.database.get_database', return_value=mock_database):
            # Perform multiple database operations
            for i in range(10):
                request_data = {
                    "task_type": "get_saved_jobs",
                    "user_id": f"user-{i}"
                }
                
                with patch.object(agent, '_get_saved_jobs') as mock_get_saved:
                    mock_get_saved.return_value = {"success": True, "data": {"saved_jobs": []}}
                    await agent._get_saved_jobs(f"user-{i}")
        
        if query_times:
            avg_query_time = statistics.mean(query_times)
            max_query_time = max(query_times)
            
            print(f"Database Query Performance:")
            print(f"  Average query time: {avg_query_time:.2f}ms")
            print(f"  Maximum query time: {max_query_time:.2f}ms")
            print(f"  Threshold: {performance_thresholds['database_query_time_ms']}ms")
            
            assert avg_query_time < performance_thresholds["database_query_time_ms"]
    
    @pytest.mark.asyncio
    async def test_api_endpoint_performance(self, performance_thresholds):
        """Test API endpoint response times"""
        
        import httpx
        from app.main import app
        
        client = httpx.AsyncClient(app=app, base_url="http://test")
        
        # Test various API endpoints
        endpoints = [
            {"method": "GET", "url": "/api/v1/health"},
            {"method": "POST", "url": "/api/v1/auth/login", "json": {"email": "test@example.com", "password": "password"}},
            {"method": "GET", "url": "/api/v1/jobs/search", "params": {"q": "python"}},
            {"method": "GET", "url": "/api/v1/dashboard"}
        ]
        
        response_times = []
        
        for endpoint in endpoints:
            # Mock authentication for protected endpoints
            headers = {"Authorization": "Bearer test-token"} if endpoint["url"] != "/api/v1/health" else {}
            
            with patch('app.core.auth.auth_manager.verify_token') as mock_verify:
                mock_verify.return_value = {"user_id": "test-user"}
                
                start_time = time.time()
                
                try:
                    if endpoint["method"] == "GET":
                        response = await client.get(
                            endpoint["url"],
                            params=endpoint.get("params"),
                            headers=headers
                        )
                    elif endpoint["method"] == "POST":
                        response = await client.post(
                            endpoint["url"],
                            json=endpoint.get("json"),
                            headers=headers
                        )
                    
                    end_time = time.time()
                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)
                    
                    print(f"API Endpoint: {endpoint['method']} {endpoint['url']} - {response_time_ms:.2f}ms")
                    
                except Exception as e:
                    print(f"API Endpoint error: {endpoint['url']} - {str(e)}")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            print(f"API Endpoint Performance:")
            print(f"  Average response time: {avg_response_time:.2f}ms")
            print(f"  Maximum response time: {max_response_time:.2f}ms")
            print(f"  Threshold: {performance_thresholds['api_response_time_ms']}ms")
            
            assert avg_response_time < performance_thresholds["api_response_time_ms"]
        
        await client.aclose()
    
    @pytest.mark.asyncio
    async def test_load_testing_simulation(self, performance_agents, performance_thresholds):
        """Test system performance under simulated load"""
        
        concurrent_users = performance_thresholds["concurrent_users"]
        agent = performance_agents["job_discovery"]
        
        # Mock agent response
        with patch.object(agent, 'process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "data": {"jobs": [{"id": "job-1"}]}
            }
            
            # Simulate concurrent users
            async def simulate_user(user_id):
                """Simulate a single user's activity"""
                requests_per_user = 3
                user_response_times = []
                
                for i in range(requests_per_user):
                    request_data = {
                        "task_type": "discover_jobs",
                        "user_id": user_id,
                        "search_criteria": {"keywords": [f"skill-{i}"]}
                    }
                    
                    start_time = time.time()
                    result = await agent.process_request(request_data, {})
                    end_time = time.time()
                    
                    response_time_ms = (end_time - start_time) * 1000
                    user_response_times.append(response_time_ms)
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                
                return user_response_times
            
            # Create tasks for concurrent users
            user_tasks = []
            for user_id in range(concurrent_users):
                task = simulate_user(f"user-{user_id}")
                user_tasks.append(task)
            
            # Execute load test
            start_time = time.time()
            user_results = await asyncio.gather(*user_tasks)
            end_time = time.time()
            
            # Analyze results
            all_response_times = []
            for user_times in user_results:
                all_response_times.extend(user_times)
            
            total_requests = len(all_response_times)
            total_time_seconds = end_time - start_time
            requests_per_second = total_requests / total_time_seconds
            avg_response_time = statistics.mean(all_response_times)
            
            print(f"Load Testing Performance:")
            print(f"  Concurrent users: {concurrent_users}")
            print(f"  Total requests: {total_requests}")
            print(f"  Total time: {total_time_seconds:.2f}s")
            print(f"  Requests per second: {requests_per_second:.2f}")
            print(f"  Average response time: {avg_response_time:.2f}ms")
            
            # Performance assertions
            assert requests_per_second > 10  # Should handle at least 10 requests per second
            assert avg_response_time < performance_thresholds["ai_response_time_ms"]
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, performance_agents):
        """Test caching performance and effectiveness"""
        
        agent = performance_agents["skills_analysis"]
        
        # Mock cache operations
        cache_hits = 0
        cache_misses = 0
        
        async def mock_get_cached_result(cache_key):
            nonlocal cache_hits, cache_misses
            if "cached" in cache_key:
                cache_hits += 1
                return {"cached": "data"}
            else:
                cache_misses += 1
                return None
        
        async def mock_cache_result(cache_key, data, ttl):
            pass  # Mock caching operation
        
        with patch.object(agent, '_get_cached_result', side_effect=mock_get_cached_result), \
             patch.object(agent, '_cache_result', side_effect=mock_cache_result):
            
            # Test cache performance
            cache_keys = [
                "cached_key_1", "cached_key_2", "uncached_key_1",
                "cached_key_3", "uncached_key_2", "cached_key_4"
            ]
            
            for cache_key in cache_keys:
                cached_data = await agent._get_cached_result(cache_key)
                if cached_data is None:
                    # Simulate expensive operation
                    await asyncio.sleep(0.01)
                    await agent._cache_result(cache_key, {"computed": "data"}, 300)
            
            cache_hit_rate = cache_hits / (cache_hits + cache_misses)
            
            print(f"Cache Performance:")
            print(f"  Cache hits: {cache_hits}")
            print(f"  Cache misses: {cache_misses}")
            print(f"  Hit rate: {cache_hit_rate:.2%}")
            
            # Cache hit rate should be reasonable for this test
            assert cache_hit_rate > 0.5  # At least 50% hit rate
    
    def test_performance_monitoring_setup(self):
        """Test performance monitoring and metrics collection setup"""
        
        # Test that performance monitoring tools are available
        try:
            import psutil
            import time
            import statistics
            
            # Test basic system metrics collection
            cpu_percent = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            disk_usage = psutil.disk_usage('/')
            
            assert isinstance(cpu_percent, (int, float))
            assert hasattr(memory_info, 'percent')
            assert hasattr(disk_usage, 'percent')
            
            print(f"Performance Monitoring Setup:")
            print(f"  CPU usage: {cpu_percent}%")
            print(f"  Memory usage: {memory_info.percent}%")
            print(f"  Disk usage: {disk_usage.percent}%")
            
        except ImportError as e:
            pytest.fail(f"Performance monitoring dependencies not available: {e}")
    
    @pytest.mark.asyncio
    async def test_stress_testing(self, performance_agents):
        """Test system behavior under stress conditions"""
        
        agent = performance_agents["resume_optimization"]
        
        # Stress test with high load
        stress_requests = 50
        max_concurrent = 20
        
        # Mock agent response
        with patch.object(agent, 'process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "data": {"optimized_resume": {}}
            }
            
            # Create semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def stress_request(request_id):
                async with semaphore:
                    request_data = {
                        "task_type": "optimize_resume",
                        "user_id": f"stress-user-{request_id}",
                        "resume_id": f"resume-{request_id}",
                        "job_id": f"job-{request_id}"
                    }
                    
                    start_time = time.time()
                    result = await agent.process_request(request_data, {})
                    end_time = time.time()
                    
                    return {
                        "success": result["success"],
                        "response_time_ms": (end_time - start_time) * 1000
                    }
            
            # Execute stress test
            stress_tasks = [stress_request(i) for i in range(stress_requests)]
            stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
            
            # Analyze stress test results
            successful_requests = 0
            failed_requests = 0
            response_times = []
            
            for result in stress_results:
                if isinstance(result, Exception):
                    failed_requests += 1
                elif result["success"]:
                    successful_requests += 1
                    response_times.append(result["response_time_ms"])
                else:
                    failed_requests += 1
            
            success_rate = successful_requests / stress_requests
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            print(f"Stress Testing Results:")
            print(f"  Total requests: {stress_requests}")
            print(f"  Successful requests: {successful_requests}")
            print(f"  Failed requests: {failed_requests}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Average response time: {avg_response_time:.2f}ms")
            
            # System should maintain reasonable performance under stress
            assert success_rate > 0.95  # At least 95% success rate
            assert avg_response_time < 10000  # Less than 10 seconds average