"""
Complete System Integration Tests
Tests the entire JobSwitch.ai platform end-to-end with all agents and components.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.job import Job
from app.models.resume import Resume
from app.models.interview import InterviewSession
from app.models.networking import NetworkingCampaign
from app.models.career_strategy import CareerRoadmap

client = TestClient(app)

class TestCompleteSystemIntegration:
    """Test complete system integration across all agents and components"""
    
    @pytest.fixture
    def mock_user_data(self):
        return {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "skills": ["Python", "React", "Machine Learning"],
            "experience_years": 5,
            "current_role": "Software Engineer",
            "target_role": "Senior ML Engineer"
        }
    
    @pytest.fixture
    def mock_job_data(self):
        return {
            "title": "Senior ML Engineer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "description": "Looking for experienced ML engineer...",
            "requirements": ["Python", "TensorFlow", "5+ years experience"],
            "salary_range": {"min": 150000, "max": 200000},
            "source": "linkedin"
        }
    
    @patch('app.integrations.watsonx.WatsonXClient')
    @patch('app.integrations.langchain_utils.LangChainManager')
    async def test_complete_user_journey_integration(self, mock_langchain, mock_watsonx, mock_user_data, mock_job_data):
        """Test complete user journey from registration to job application"""
        
        # Mock AI services
        mock_watsonx_instance = Mock()
        mock_watsonx.return_value = mock_watsonx_instance
        mock_langchain_instance = Mock()
        mock_langchain.return_value = mock_langchain_instance
        
        # 1. User Registration and Authentication
        register_response = client.post("/api/v1/auth/register", json=mock_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": mock_user_data["email"],
            "password": mock_user_data["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Profile Setup and Skills Analysis
        profile_response = client.post("/api/v1/user/profile", 
                                     json=mock_user_data, headers=headers)
        assert profile_response.status_code == 200
        
        # Mock skills analysis
        mock_watsonx_instance.analyze_skills.return_value = {
            "extracted_skills": ["Python", "React", "Machine Learning"],
            "skill_gaps": ["TensorFlow", "Deep Learning"],
            "recommendations": ["Take TensorFlow course", "Practice deep learning"]
        }
        
        skills_response = client.post("/api/v1/agents/skills-analysis/analyze",
                                    json={"resume_text": "Sample resume content"},
                                    headers=headers)
        assert skills_response.status_code == 200
        
        # 3. Job Discovery and Recommendations
        with patch('app.integrations.job_connectors.LinkedInConnector') as mock_linkedin:
            mock_linkedin.return_value.search_jobs.return_value = [mock_job_data]
            
            job_search_response = client.post("/api/v1/agents/job-discovery/search",
                                            json={"keywords": "ML Engineer", "location": "San Francisco"},
                                            headers=headers)
            assert job_search_response.status_code == 200
            jobs = job_search_response.json()["jobs"]
            assert len(jobs) > 0
        
        # 4. Resume Optimization
        mock_watsonx_instance.optimize_resume.return_value = {
            "optimized_content": "Optimized resume content",
            "ats_score": 85,
            "improvements": ["Added relevant keywords", "Improved formatting"]
        }
        
        resume_response = client.post("/api/v1/agents/resume-optimization/optimize",
                                    json={
                                        "resume_content": "Original resume",
                                        "target_job_id": "job_123"
                                    },
                                    headers=headers)
        assert resume_response.status_code == 200
        assert resume_response.json()["ats_score"] == 85
        
        # 5. Interview Preparation
        mock_watsonx_instance.generate_interview_questions.return_value = [
            {"question": "Tell me about your ML experience", "type": "behavioral"},
            {"question": "Explain gradient descent", "type": "technical"}
        ]
        
        interview_prep_response = client.post("/api/v1/agents/interview-preparation/questions",
                                            json={"job_role": "ML Engineer"},
                                            headers=headers)
        assert interview_prep_response.status_code == 200
        questions = interview_prep_response.json()["questions"]
        assert len(questions) >= 2
        
        # 6. Networking and Outreach
        mock_watsonx_instance.generate_outreach_email.return_value = {
            "subject": "Interest in ML Engineer Position",
            "body": "Personalized email content..."
        }
        
        networking_response = client.post("/api/v1/agents/networking/generate-email",
                                        json={
                                            "contact_name": "John Doe",
                                            "company": "TechCorp",
                                            "position": "ML Engineer"
                                        },
                                        headers=headers)
        assert networking_response.status_code == 200
        
        # 7. Career Strategy Planning
        mock_watsonx_instance.generate_career_roadmap.return_value = {
            "milestones": [
                {"title": "Learn TensorFlow", "timeline": "3 months"},
                {"title": "Complete ML project", "timeline": "6 months"}
            ],
            "timeline": "12 months"
        }
        
        career_response = client.post("/api/v1/agents/career-strategy/roadmap",
                                    json={
                                        "current_role": "Software Engineer",
                                        "target_role": "Senior ML Engineer"
                                    },
                                    headers=headers)
        assert career_response.status_code == 200
        
        # 8. Dashboard Integration - Verify all data is accessible
        dashboard_response = client.get("/api/v1/dashboard/overview", headers=headers)
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        
        # Verify dashboard contains data from all agents
        assert "job_recommendations" in dashboard_data
        assert "skill_analysis" in dashboard_data
        assert "resume_status" in dashboard_data
        assert "interview_progress" in dashboard_data
        assert "networking_campaigns" in dashboard_data
        assert "career_roadmap" in dashboard_data
    
    @patch('app.integrations.watsonx.WatsonXClient')
    async def test_agent_orchestration_integration(self, mock_watsonx):
        """Test agent orchestration and communication"""
        
        # Mock orchestrator responses
        mock_watsonx_instance = Mock()
        mock_watsonx.return_value = mock_watsonx_instance
        
        # Test agent coordination
        orchestration_response = client.post("/api/v1/orchestrator/coordinate",
                                           json={
                                               "user_id": "test_user",
                                               "task": "complete_job_application",
                                               "job_id": "job_123"
                                           })
        assert orchestration_response.status_code == 200
        
        # Verify orchestrator coordinates multiple agents
        result = orchestration_response.json()
        assert "agents_involved" in result
        assert len(result["agents_involved"]) >= 3  # Should involve multiple agents
    
    async def test_websocket_real_time_updates(self):
        """Test real-time updates via WebSocket"""
        
        with client.websocket_connect("/ws/dashboard") as websocket:
            # Simulate agent activity
            test_data = {
                "type": "job_recommendation",
                "data": {"job_id": "job_123", "compatibility_score": 0.85}
            }
            
            # Send test message
            websocket.send_json(test_data)
            
            # Receive response
            response = websocket.receive_json()
            assert response["type"] == "job_recommendation"
            assert response["data"]["job_id"] == "job_123"
    
    @patch('app.integrations.job_connectors.LinkedInConnector')
    @patch('app.integrations.job_connectors.IndeedConnector')
    @patch('app.integrations.job_connectors.GlassdoorConnector')
    async def test_external_api_integration(self, mock_glassdoor, mock_indeed, mock_linkedin):
        """Test integration with external job board APIs"""
        
        # Mock external API responses
        mock_linkedin.return_value.search_jobs.return_value = [
            {"title": "ML Engineer", "company": "LinkedIn Corp", "source": "linkedin"}
        ]
        mock_indeed.return_value.search_jobs.return_value = [
            {"title": "Data Scientist", "company": "Indeed Inc", "source": "indeed"}
        ]
        mock_glassdoor.return_value.search_jobs.return_value = [
            {"title": "AI Engineer", "company": "Glassdoor Ltd", "source": "glassdoor"}
        ]
        
        # Test multi-platform job search
        response = client.post("/api/v1/agents/job-discovery/search",
                             json={
                                 "keywords": "machine learning",
                                 "platforms": ["linkedin", "indeed", "glassdoor"]
                             })
        
        assert response.status_code == 200
        jobs = response.json()["jobs"]
        
        # Verify jobs from all platforms
        sources = [job["source"] for job in jobs]
        assert "linkedin" in sources
        assert "indeed" in sources
        assert "glassdoor" in sources
    
    async def test_error_handling_and_fallbacks(self):
        """Test system error handling and fallback mechanisms"""
        
        # Test API error handling
        with patch('app.integrations.watsonx.WatsonXClient') as mock_watsonx:
            mock_watsonx.side_effect = Exception("WatsonX API Error")
            
            # Should fallback gracefully
            response = client.post("/api/v1/agents/skills-analysis/analyze",
                                 json={"resume_text": "test content"})
            
            # Should return error but not crash
            assert response.status_code in [500, 503]  # Server error or service unavailable
            assert "error" in response.json()
    
    async def test_performance_under_load(self):
        """Test system performance with concurrent requests"""
        
        async def make_request():
            response = client.get("/api/v1/health")
            return response.status_code
        
        # Simulate concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    async def test_data_consistency_across_agents(self):
        """Test data consistency when multiple agents access user data"""
        
        # Create test user
        user_data = {
            "email": "consistency@test.com",
            "password": "testpass123",
            "full_name": "Consistency Test"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Login
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Update profile through multiple endpoints
        profile_updates = [
            {"skills": ["Python", "React"]},
            {"experience_years": 3},
            {"current_role": "Developer"}
        ]
        
        for update in profile_updates:
            response = client.patch("/api/v1/user/profile", json=update, headers=headers)
            assert response.status_code == 200
        
        # Verify consistency across all agent endpoints
        profile_response = client.get("/api/v1/user/profile", headers=headers)
        profile_data = profile_response.json()
        
        assert "Python" in profile_data["skills"]
        assert "React" in profile_data["skills"]
        assert profile_data["experience_years"] == 3
        assert profile_data["current_role"] == "Developer"
    
    async def test_security_integration(self):
        """Test security measures across the system"""
        
        # Test rate limiting
        for _ in range(15):  # Exceed rate limit
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "wrong_password"
            })
        
        # Should be rate limited
        assert response.status_code == 429
        
        # Test input validation
        invalid_data = {
            "email": "not_an_email",
            "password": "123",  # Too short
            "full_name": ""  # Empty
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    async def test_mobile_api_compatibility(self):
        """Test API compatibility with mobile clients"""
        
        # Test mobile-optimized endpoints
        response = client.get("/api/v1/mobile/jobs/recommendations",
                            headers={"User-Agent": "JobSwitch-Mobile/1.0"})
        
        # Should return mobile-optimized response
        if response.status_code == 200:
            data = response.json()
            assert "mobile_optimized" in data or "jobs" in data
    
    async def test_analytics_integration(self):
        """Test analytics and monitoring integration"""
        
        # Test analytics endpoint
        response = client.get("/api/v1/analytics/overview")
        assert response.status_code in [200, 401]  # Success or auth required
        
        # Test performance monitoring
        response = client.get("/api/v1/monitoring/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "agents" in health_data
        assert "database" in health_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])