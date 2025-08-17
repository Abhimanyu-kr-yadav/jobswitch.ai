"""
Integration tests for external API integrations
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import aiohttp
from datetime import datetime

from app.integrations.job_connectors import JobConnectors
from app.integrations.watsonx import WatsonXClient
from app.integrations.langchain_utils import LangChainAgentManager


class TestExternalAPIIntegrations:
    """Test cases for external API integrations"""
    
    @pytest.fixture
    def job_connectors(self):
        """Create JobConnectors instance for testing"""
        return JobConnectors()
    
    @pytest.fixture
    def watsonx_client(self, mock_settings):
        """Create WatsonX client for testing"""
        return WatsonXClient(mock_settings)
    
    @pytest.fixture
    def langchain_manager(self):
        """Create LangChain manager for testing"""
        return LangChainAgentManager()
    
    @pytest.mark.asyncio
    async def test_linkedin_job_search_integration(self, job_connectors):
        """Test LinkedIn job search API integration"""
        search_params = {
            "keywords": "software engineer",
            "location": "san francisco",
            "job_type": "full-time"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock LinkedIn API response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "jobs": [
                    {
                        "id": "linkedin-job-1",
                        "title": "Software Engineer",
                        "company": "LinkedIn Corp",
                        "location": "San Francisco, CA",
                        "description": "We are looking for a software engineer...",
                        "posted_date": "2025-01-01"
                    }
                ]
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await job_connectors.search_linkedin_jobs(search_params)
            
            assert result["success"] is True
            assert "jobs" in result
            assert len(result["jobs"]) > 0
            assert result["jobs"][0]["source"] == "linkedin"
    
    @pytest.mark.asyncio
    async def test_indeed_job_search_integration(self, job_connectors):
        """Test Indeed job search API integration"""
        search_params = {
            "keywords": "python developer",
            "location": "remote",
            "salary_min": 80000
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock Indeed API response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "results": [
                    {
                        "jobkey": "indeed-job-1",
                        "jobtitle": "Python Developer",
                        "company": "TechCorp",
                        "formattedLocation": "Remote",
                        "snippet": "Looking for Python developer with 3+ years experience",
                        "date": "2025-01-01"
                    }
                ]
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await job_connectors.search_indeed_jobs(search_params)
            
            assert result["success"] is True
            assert "jobs" in result
            assert len(result["jobs"]) > 0
            assert result["jobs"][0]["source"] == "indeed"
    
    @pytest.mark.asyncio
    async def test_glassdoor_job_search_integration(self, job_connectors):
        """Test Glassdoor job search API integration"""
        search_params = {
            "keywords": "full stack developer",
            "location": "new york",
            "company_rating_min": 4.0
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock Glassdoor API response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "response": {
                    "jobs": [
                        {
                            "jobId": "glassdoor-job-1",
                            "jobTitle": "Full Stack Developer",
                            "employer": {
                                "name": "StartupCorp",
                                "overallRating": 4.2
                            },
                            "locationName": "New York, NY",
                            "jobDescription": "Full stack developer position...",
                            "ageInDays": 5
                        }
                    ]
                }
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await job_connectors.search_glassdoor_jobs(search_params)
            
            assert result["success"] is True
            assert "jobs" in result
            assert len(result["jobs"]) > 0
            assert result["jobs"][0]["source"] == "glassdoor"
    
    @pytest.mark.asyncio
    async def test_watsonx_text_generation(self, watsonx_client):
        """Test WatsonX text generation API"""
        prompt = "Extract skills from the following resume: Software Engineer with 5 years Python experience"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock WatsonX API response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "results": [
                    {
                        "generated_text": '{"skills": ["Python", "Software Engineering"], "experience_years": 5}'
                    }
                ]
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await watsonx_client.generate_text(prompt)
            
            assert result["success"] is True
            assert "generated_text" in result
            assert "Python" in result["generated_text"]
    
    @pytest.mark.asyncio
    async def test_watsonx_error_handling(self, watsonx_client):
        """Test WatsonX API error handling"""
        prompt = "Test prompt"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock API error response
            mock_response = Mock()
            mock_response.status = 429  # Rate limit error
            mock_response.json = AsyncMock(return_value={
                "error": "Rate limit exceeded"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await watsonx_client.generate_text(prompt)
            
            assert result["success"] is False
            assert "error" in result
            assert "rate limit" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_langchain_agent_processing(self, langchain_manager):
        """Test LangChain agent processing"""
        chain_config = {
            "chain_type": "skill_extraction",
            "model": "gpt-3.5-turbo",
            "temperature": 0.1
        }
        
        input_data = {
            "text": "Software Engineer with Python, React, and AWS experience"
        }
        
        with patch.object(langchain_manager, '_execute_chain') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": {
                    "extracted_skills": ["Python", "React", "AWS"],
                    "confidence_scores": [0.95, 0.90, 0.85]
                },
                "processing_time_ms": 150
            }
            
            result = await langchain_manager.process_with_chain(chain_config, input_data)
            
            assert result["success"] is True
            assert "extracted_skills" in result["result"]
            assert len(result["result"]["extracted_skills"]) == 3
    
    @pytest.mark.asyncio
    async def test_job_board_aggregation(self, job_connectors):
        """Test aggregating jobs from multiple job boards"""
        search_params = {
            "keywords": "data scientist",
            "location": "seattle",
            "sources": ["linkedin", "indeed", "glassdoor"]
        }
        
        with patch.object(job_connectors, 'search_linkedin_jobs') as mock_linkedin, \
             patch.object(job_connectors, 'search_indeed_jobs') as mock_indeed, \
             patch.object(job_connectors, 'search_glassdoor_jobs') as mock_glassdoor:
            
            # Mock responses from different sources
            mock_linkedin.return_value = {
                "success": True,
                "jobs": [{"id": "linkedin-1", "title": "Data Scientist", "source": "linkedin"}]
            }
            mock_indeed.return_value = {
                "success": True,
                "jobs": [{"id": "indeed-1", "title": "Data Scientist", "source": "indeed"}]
            }
            mock_glassdoor.return_value = {
                "success": True,
                "jobs": [{"id": "glassdoor-1", "title": "Data Scientist", "source": "glassdoor"}]
            }
            
            result = await job_connectors.search_all_sources(search_params)
            
            assert result["success"] is True
            assert len(result["jobs"]) == 3
            # Verify jobs from all sources are included
            sources = [job["source"] for job in result["jobs"]]
            assert "linkedin" in sources
            assert "indeed" in sources
            assert "glassdoor" in sources
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, job_connectors):
        """Test API rate limiting handling"""
        search_params = {"keywords": "engineer", "location": "sf"}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # First call succeeds
            mock_response_success = Mock()
            mock_response_success.status = 200
            mock_response_success.json = AsyncMock(return_value={"jobs": []})
            
            # Second call hits rate limit
            mock_response_rate_limit = Mock()
            mock_response_rate_limit.status = 429
            mock_response_rate_limit.json = AsyncMock(return_value={"error": "Rate limit exceeded"})
            
            mock_get.return_value.__aenter__.side_effect = [
                mock_response_success,
                mock_response_rate_limit
            ]
            
            # First call should succeed
            result1 = await job_connectors.search_linkedin_jobs(search_params)
            assert result1["success"] is True
            
            # Second call should handle rate limit gracefully
            result2 = await job_connectors.search_linkedin_jobs(search_params)
            assert result2["success"] is False
            assert "rate limit" in result2["error"].lower()
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, job_connectors):
        """Test API timeout handling"""
        search_params = {"keywords": "developer", "location": "la"}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock timeout exception
            mock_get.side_effect = asyncio.TimeoutError("Request timeout")
            
            result = await job_connectors.search_linkedin_jobs(search_params)
            
            assert result["success"] is False
            assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_api_authentication(self, watsonx_client):
        """Test API authentication handling"""
        prompt = "Test authentication"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock authentication error
            mock_response = Mock()
            mock_response.status = 401
            mock_response.json = AsyncMock(return_value={
                "error": "Invalid API key"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await watsonx_client.generate_text(prompt)
            
            assert result["success"] is False
            assert "authentication" in result["error"].lower() or "api key" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, job_connectors):
        """Test handling of concurrent API calls"""
        search_params_list = [
            {"keywords": "python", "location": "sf"},
            {"keywords": "java", "location": "ny"},
            {"keywords": "react", "location": "seattle"}
        ]
        
        with patch.object(job_connectors, 'search_linkedin_jobs') as mock_search:
            mock_search.return_value = {
                "success": True,
                "jobs": [{"id": "job-1", "title": "Developer"}]
            }
            
            # Execute concurrent searches
            tasks = [
                job_connectors.search_linkedin_jobs(params)
                for params in search_params_list
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(result["success"] for result in results)
            assert mock_search.call_count == 3
    
    @pytest.mark.asyncio
    async def test_api_response_validation(self, job_connectors):
        """Test API response validation"""
        search_params = {"keywords": "engineer", "location": "boston"}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock invalid response format
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "invalid_format": "missing required fields"
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await job_connectors.search_linkedin_jobs(search_params)
            
            # Should handle invalid response gracefully
            assert result["success"] is False
            assert "invalid response" in result["error"].lower() or "validation" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_api_retry_mechanism(self, watsonx_client):
        """Test API retry mechanism for transient failures"""
        prompt = "Test retry mechanism"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock transient failure followed by success
            mock_response_fail = Mock()
            mock_response_fail.status = 503  # Service unavailable
            mock_response_fail.json = AsyncMock(return_value={"error": "Service temporarily unavailable"})
            
            mock_response_success = Mock()
            mock_response_success.status = 200
            mock_response_success.json = AsyncMock(return_value={
                "results": [{"generated_text": "Success after retry"}]
            })
            
            mock_post.return_value.__aenter__.side_effect = [
                mock_response_fail,
                mock_response_success
            ]
            
            result = await watsonx_client.generate_text(prompt, max_retries=2)
            
            assert result["success"] is True
            assert "Success after retry" in result["generated_text"]
            assert mock_post.call_count == 2  # One failure, one success