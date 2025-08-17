"""
Unit tests for Job Discovery Agent
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.agents.job_discovery import JobDiscoveryAgent


class TestJobDiscoveryAgent:
    """Test cases for JobDiscoveryAgent class"""
    
    @pytest.fixture
    def job_discovery_agent(self, mock_watsonx_client, mock_langchain_manager):
        """Create a JobDiscoveryAgent instance for testing"""
        return JobDiscoveryAgent(mock_watsonx_client, mock_langchain_manager)
    
    def test_agent_initialization(self, job_discovery_agent):
        """Test job discovery agent initialization"""
        assert job_discovery_agent.agent_id is not None
        assert job_discovery_agent.agent_type == "job_discovery"
        assert job_discovery_agent.watsonx is not None
        assert job_discovery_agent.langchain is not None
    
    @pytest.mark.asyncio
    async def test_discover_jobs(self, job_discovery_agent, sample_user_profile, mock_external_apis):
        """Test job discovery functionality"""
        with patch('app.integrations.job_connectors.JobConnectors') as mock_connectors:
            # Mock job connectors
            mock_connector_instance = Mock()
            mock_connector_instance.search_jobs = AsyncMock(return_value={
                "success": True,
                "jobs": [
                    {
                        "id": "job-1",
                        "title": "Software Engineer",
                        "company": "TechCorp",
                        "location": "San Francisco, CA",
                        "description": "Looking for a Python developer...",
                        "source": "linkedin"
                    }
                ]
            })
            mock_connectors.return_value = mock_connector_instance
            
            # Test job discovery
            result = await job_discovery_agent._discover_jobs(
                sample_user_profile,
                {"search_query": "python developer", "location": "san francisco"}
            )
            
            assert result["success"] is True
            assert "jobs" in result["data"]
            assert len(result["data"]["jobs"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, job_discovery_agent, sample_user_profile, sample_job_posting):
        """Test job recommendation generation"""
        # Mock job data
        jobs = [sample_job_posting]
        
        result = await job_discovery_agent._generate_recommendations(
            sample_user_profile,
            {"jobs": jobs, "limit": 5}
        )
        
        assert result["success"] is True
        assert "recommendations" in result["data"]
        assert "total_jobs_analyzed" in result["data"]
    
    @pytest.mark.asyncio
    async def test_calculate_job_compatibility(self, job_discovery_agent, sample_user_profile, sample_job_posting):
        """Test job compatibility scoring"""
        compatibility = await job_discovery_agent._calculate_job_compatibility(
            sample_user_profile,
            sample_job_posting
        )
        
        assert isinstance(compatibility, dict)
        assert "overall_score" in compatibility
        assert "skill_match" in compatibility
        assert "experience_match" in compatibility
        assert "location_match" in compatibility
        assert 0 <= compatibility["overall_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_search_jobs_by_criteria(self, job_discovery_agent, sample_user_profile):
        """Test job search by specific criteria"""
        search_criteria = {
            "keywords": ["python", "react"],
            "location": "san francisco",
            "job_type": "full-time",
            "salary_min": 80000
        }
        
        with patch('app.integrations.job_connectors.JobConnectors') as mock_connectors:
            mock_connector_instance = Mock()
            mock_connector_instance.search_jobs = AsyncMock(return_value={
                "success": True,
                "jobs": [{"id": "job-1", "title": "Python Developer"}]
            })
            mock_connectors.return_value = mock_connector_instance
            
            result = await job_discovery_agent._search_jobs_by_criteria(
                sample_user_profile,
                search_criteria
            )
            
            assert result["success"] is True
            assert "jobs" in result["data"]
    
    @pytest.mark.asyncio
    async def test_save_job_for_user(self, job_discovery_agent, mock_database):
        """Test saving job for user"""
        job_data = {
            "job_id": "job-123",
            "user_id": "user-123",
            "saved_at": datetime.utcnow().isoformat()
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await job_discovery_agent._save_job_for_user(job_data)
            
            assert result["success"] is True
            mock_database.add.assert_called_once()
            mock_database.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_saved_jobs(self, job_discovery_agent, mock_database):
        """Test retrieving saved jobs for user"""
        user_id = "user-123"
        
        # Mock saved jobs
        mock_saved_job = Mock()
        mock_saved_job.to_dict.return_value = {
            "job_id": "job-123",
            "title": "Software Engineer",
            "saved_at": datetime.utcnow().isoformat()
        }
        mock_database.query.return_value.filter.return_value.all.return_value = [mock_saved_job]
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await job_discovery_agent._get_saved_jobs(user_id)
            
            assert result["success"] is True
            assert "saved_jobs" in result["data"]
            assert len(result["data"]["saved_jobs"]) == 1
    
    @pytest.mark.asyncio
    async def test_track_job_application(self, job_discovery_agent, mock_database):
        """Test job application tracking"""
        application_data = {
            "user_id": "user-123",
            "job_id": "job-123",
            "status": "applied",
            "applied_at": datetime.utcnow().isoformat()
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await job_discovery_agent._track_job_application(application_data)
            
            assert result["success"] is True
            mock_database.add.assert_called_once()
            mock_database.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_job_market_insights(self, job_discovery_agent, sample_user_profile):
        """Test job market insights generation"""
        result = await job_discovery_agent._get_job_market_insights(
            sample_user_profile,
            {"location": "san francisco", "role": "software engineer"}
        )
        
        assert result["success"] is True
        assert "market_insights" in result["data"]
        assert "salary_trends" in result["data"]["market_insights"]
        assert "demand_analysis" in result["data"]["market_insights"]
    
    @pytest.mark.asyncio
    async def test_process_request_discover_jobs(self, job_discovery_agent, sample_user_profile):
        """Test process_request for job discovery"""
        request_data = {
            "task_type": "discover_jobs",
            "user_id": "user-123",
            "search_criteria": {
                "keywords": ["python"],
                "location": "san francisco"
            }
        }
        
        with patch.object(job_discovery_agent, '_discover_jobs') as mock_discover:
            mock_discover.return_value = {
                "success": True,
                "data": {"jobs": [{"id": "job-1"}]}
            }
            
            result = await job_discovery_agent.process_request(request_data, {})
            
            assert result["success"] is True
            mock_discover.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_generate_recommendations(self, job_discovery_agent):
        """Test process_request for recommendation generation"""
        request_data = {
            "task_type": "generate_recommendations",
            "user_id": "user-123",
            "limit": 10
        }
        
        with patch.object(job_discovery_agent, '_generate_recommendations') as mock_recommend:
            mock_recommend.return_value = {
                "success": True,
                "data": {"recommendations": []}
            }
            
            result = await job_discovery_agent.process_request(request_data, {})
            
            assert result["success"] is True
            mock_recommend.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recommendations(self, job_discovery_agent, sample_user_profile):
        """Test get_recommendations method"""
        with patch.object(job_discovery_agent, '_generate_recommendations') as mock_recommend:
            mock_recommend.return_value = {
                "success": True,
                "data": {
                    "recommendations": [
                        {
                            "title": "Software Engineer",
                            "company": "TechCorp",
                            "match_score": 0.85,
                            "reason": "Strong skill match"
                        }
                    ]
                }
            }
            
            recommendations = await job_discovery_agent.get_recommendations(sample_user_profile)
            
            assert len(recommendations) > 0
            assert "title" in recommendations[0]
            assert "match_score" in recommendations[0]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, job_discovery_agent):
        """Test error handling in job discovery"""
        request_data = {
            "task_type": "invalid_task",
            "user_id": "user-123"
        }
        
        result = await job_discovery_agent.process_request(request_data, {})
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_job_filtering(self, job_discovery_agent, sample_user_profile):
        """Test job filtering based on user preferences"""
        jobs = [
            {
                "id": "job-1",
                "title": "Software Engineer",
                "salary_range": {"min": 90000, "max": 120000},
                "location": "San Francisco, CA",
                "job_type": "full-time"
            },
            {
                "id": "job-2",
                "title": "Junior Developer",
                "salary_range": {"min": 50000, "max": 70000},
                "location": "New York, NY",
                "job_type": "part-time"
            }
        ]
        
        filtered_jobs = await job_discovery_agent._filter_jobs_by_preferences(
            jobs,
            sample_user_profile["preferences"]
        )
        
        assert len(filtered_jobs) <= len(jobs)
        # Should filter based on salary range and job type preferences
    
    @pytest.mark.asyncio
    async def test_job_deduplication(self, job_discovery_agent):
        """Test job deduplication functionality"""
        jobs = [
            {"id": "job-1", "title": "Software Engineer", "company": "TechCorp"},
            {"id": "job-2", "title": "Software Engineer", "company": "TechCorp"},  # Duplicate
            {"id": "job-3", "title": "Python Developer", "company": "DataCorp"}
        ]
        
        deduplicated_jobs = await job_discovery_agent._deduplicate_jobs(jobs)
        
        assert len(deduplicated_jobs) < len(jobs)
        # Should remove duplicates based on title and company